import logging
import asyncio
import re
import json
import ast
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import httpx
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import BaseTool, StructuredTool

# MCP Imports
from mcp import ClientSession
from mcp.client.sse import sse_client

from ai_service.core.config import settings
from ai_service.core.llm_factory import llm_manager
from ai_service.core.prompt_guard import (
    prompt_guard, 
    validate_trip_request, 
    validate_refine_request, 
    validate_chat_request
)
from ai_service.schemas.api_models import TripRequest, ChatRequest, RefineRequest, BudgetAnalysisRequest

logger = logging.getLogger("uvicorn")

class TravelAgent:
    """AI-powered travel planning agent with LLM integration."""
    
    def __init__(self):
        self.manager = llm_manager
        # MCP server endpoint (Docker internal network)
        self.mcp_url = "http://mcp-server:8000/sse"

    async def answer_question(self, req: ChatRequest) -> Dict[str, str]:
        """
        Answers a user question based on the provided context (trip plan).
        """
        # Prompt Injection Protection
        is_valid, clean_question, error = validate_chat_request(req.question)
        if not is_valid:
            logger.warning(f"🚨 Blocked chat request: {error}")
            return {"answer": "I couldn't process your question. Please try rephrasing it."}
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""{prompt_guard.get_safety_prefix()}
You are a helpful travel assistant. Answer the user's question concisely based strictly on the provided trip context."""),
                ("user", "Trip Context:\n{context}\n\nUser Question: {question}")
            ])
            
            messages = prompt.format_messages(
                context=req.context,
                question=prompt_guard.wrap_user_input(clean_question)
            )
            
            response = await self.manager.invoke(messages, preferred_model=req.model)
            content = response.content if hasattr(response, 'content') else str(response)
            
            return {"answer": content}
            
        except Exception as e:
            logger.error(f"❌ Chat Error: {e}")
            return {"answer": "I'm sorry, I encountered an error while processing your question."}

    async def refine_trip(self, req: RefineRequest) -> Dict[str, Any]:
        """
        Refines an existing trip plan based on user instructions.
        """
        # 🛡️ Prompt Injection Protection
        is_valid, clean_instructions, error = validate_refine_request(req.instructions)
        if not is_valid:
            logger.warning(f"🚨 Blocked refine request: {error}")
            raise ValueError("Invalid instructions detected. Please try rephrasing.")
        
        # Prompt Setup:
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{prompt_guard.get_safety_prefix()}
You are a precise JSON-speaking travel agent. Modify the plan based on instructions."""),
            ("user", """
             Current Plan:
             {current_plan}
             
             Instructions:
             {instructions}
             
             CRITICAL OUTPUT RULES:
             1. Return ONLY the full updated JSON object.
             2. NO Markdown, NO explanations, NO code blocks.
             3. Use double quotes (") for all keys and strings.
             4. Escape internal quotes (e.g., "City of \\"Love\\"").
             5. Ensure commas separate all fields correctly.
             
             Return Structure:
             {{
                "summary": "...",
                "budget_breakdown": {{ ... }},
                "itinerary": [ ... ]
             }}
             """)
        ])

        messages = prompt.format_messages(
            current_plan=json.dumps(req.current_plan),
            instructions=prompt_guard.wrap_user_input(clean_instructions)
        )
        
        try:
            response = await self.manager.invoke(messages, preferred_model=req.model)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # 1. Clean Markdown
            cleaned_content = self._clean_json_string(content)
            
            # 2. Try strict JSON parse
            try:
                result = json.loads(cleaned_content)
            except json.JSONDecodeError:
                # 3. Fallback: Try parsing as a Python dict (handles single quotes/loose syntax)
                try:
                    logger.warning("⚠️ JSON parse failed, attempting AST eval...")
                    result = ast.literal_eval(cleaned_content)
                except Exception:
                    # 4. Critical Fail - Log the bad content
                    logger.error(f"❌ Failed to parse AI response. Raw content:\n{cleaned_content[:500]}...")
                    raise ValueError("AI returned invalid format.")

            return result
            
        except Exception as e:
            logger.error(f"❌ Refine Failed: {e}")
            raise e

    async def plan_trip(self, req: TripRequest, analyzed_vibe: str) -> Dict[str, Any]:
        # 🛡️ Prompt Injection Protection
        is_valid, sanitized, error = validate_trip_request(
            req.destination, req.origin, req.interest
        )
        if not is_valid:
            logger.warning(f"🚨 Blocked trip request: {error}")
            return {
                "summary": "Request blocked due to invalid input. Please check your entries.",
                "itinerary": [],
                "budget_breakdown": {},
                "analyzed_vibe": "Error"
            }
        
        # Prompt Setup:
        parser = JsonOutputParser()
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{prompt_guard.get_safety_prefix()}
You are an expert travel agent. Create a detailed itinerary. OUTPUT MUST BE RAW JSON ONLY."""),
            ("user", """
             Plan a {duration}-day trip from {origin} to {destination}.
             Budget: {budget} {currency}.
             Interests: {interest}.
             Vibe: {vibe}.
             
             IMPORTANT: Return ONLY valid JSON. No markdown formatting, no explanations.
             Structure:
             {{
                "summary": "...",
                "budget_breakdown": {{ "Flights": 0, "Accommodation": 0, "Food": 0, "Activities": 0, "Transport": 0 }},
                "itinerary": [ {{ "day": 1, "title": "...", "activities": ["..."] }} ]
             }}
             """)
        ])

        messages = prompt.format_messages(
            duration=req.duration, 
            origin=sanitized["origin"], 
            destination=sanitized["destination"],
            budget=req.budget, 
            currency=req.currency, 
            interest=prompt_guard.wrap_user_input(sanitized["interests"]),
            vibe=analyzed_vibe
        )
        
        try:
            response = await self.manager.invoke(messages, preferred_model=req.model)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # JSON Cleaning & Parsing
            cleaned_content = self._clean_json_string(content)
            
            try:
                result = parser.parse(cleaned_content)
            except Exception:
                logger.warning(f"⚠️ Standard parsing failed, attempting raw json load.")
                result = json.loads(cleaned_content)

            if not isinstance(result, dict):
                # Critical Fail - Log the bad content
                logger.error(f"❌ AI did not return a dictionary. Raw content:\n{cleaned_content[:500]}...")
                raise ValueError("AI returned invalid format (not a dictionary)")

            result["analyzed_vibe"] = analyzed_vibe

            # --- n8n Automation (Fire & Forget) ---
            # Run in background to avoid blocking response
            if result and "itinerary" in result and req.email:
                asyncio.create_task(self._trigger_automation(result, req))

            return result
            
        except Exception as e:
            logger.error(f"❌ AI Execution Failed: {e}")
            return {
                "summary": f"AI generation failed: {str(e)}",
                "itinerary": [],
                "budget_breakdown": {},
                "analyzed_vibe": "Error"
            }
        
    async def analyze_budget(self, req: BudgetAnalysisRequest) -> Dict[str, Any]:
        """
        Asks the AI to split the budget based on real-world costs for the destination.
        """
        parser = JsonOutputParser()
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a financial travel expert. Analyze the budget and provide a realistic breakdown."),
            ("user", """
             Create a budget breakdown for a {duration}-day trip to {destination} from {origin}.
             Total Budget: {budget} {currency}.
             Traveler Interests: {interest}.
             
             Task:
             1. Estimate flight costs from {origin} to {destination} for this duration.
             2. Estimate accommodation (hotels/Airbnb) costs.
             3. Estimate food, activities, and local transport.
             4. Ensure the total sums up to approximately the provided budget.
             
             CRITICAL OUTPUT RULES:
             - Return ONLY valid JSON.
             - Format: {{ "breakdown": {{ "Flights": 0, "Accommodation": 0, "Food": 0, "Activities": 0, "Transport": 0 }} }}
             - Values should be integers (no currency symbols).
             """)
        ])

        messages = prompt.format_messages(
            duration=req.duration,
            destination=req.destination,
            origin=req.origin,
            budget=req.budget,
            currency=req.currency,
            interest=req.interest
        )
        
        try:
            # Use the manager with the requested model
            response = await self.manager.invoke(messages, preferred_model=req.model)
            content = response.content if hasattr(response, 'content') else str(response)
            cleaned_content = self._clean_json_string(content)
            
            return parser.parse(cleaned_content)
            
        except Exception as e:
            logger.error(f"❌ Budget Analysis Failed: {e}")
            # Fallback to a "safe" even split if AI fails, to prevent crash
            return {
                "breakdown": {
                    "Flights": 0, "Accommodation": 0, "Food": 0, "Activities": 0, "Transport": 0
                }
            }

    async def _trigger_automation(self, trip_data: dict, req: TripRequest):
        """Silently sends trip data to n8n webhook for email automation."""
        print(f"DEBUG: Attempting to send data to n8n at {settings.N8N_WEBHOOK_URL}")
        try:
            # Calculate dynamic dates starting from today
            start_date_obj = datetime.now()
            end_date_obj = start_date_obj + timedelta(days=req.duration)
            
            # Extract email from request (fallback to default)
            user_email = req.email

            # this check is just to make sure, we alredy cheak before calling this function, but just in case to prevent any issues with n8n
            if not user_email:
                logger.warning("⚠️ No email provided in request, not sending to n8n.")
                return
            
            payload = {
                "email": user_email,
                "summary": f"Trip to {req.destination}: {trip_data.get('summary', '')[:200]}...",
                "full_itinerary": str(trip_data.get("itinerary", [])),
                "start_date": start_date_obj.strftime("%Y-%m-%d"),
                "end_date": end_date_obj.strftime("%Y-%m-%d")
            }
            
            async with httpx.AsyncClient() as client:
                # Short timeout to prevent hanging if n8n is down
                resp = await client.post(settings.N8N_WEBHOOK_URL, json=payload, timeout=3.0)
                print(f"DEBUG: n8n response status: {resp.status_code}")
                
        except Exception as e:
            print(f"ERROR sending to n8n: {e}")

    def _clean_json_string(self, json_str: str) -> str:
        """
        Strips Markdown code fences (```json) from AI responses
        to prevent JSON parser failures.
        """
        pattern = r"```json(.*?)```"
        match = re.search(pattern, json_str, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
        else:
            start = json_str.find("{")
            end = json_str.rfind("}")
            if start != -1 and end != -1:
                json_str = json_str[start : end + 1]
        
        return json_str

    async def _fetch_mcp_tools(self) -> List[BaseTool]:
        """
        Connects to MCP server manually using the official SDK.
        """
        lc_tools = []
        try:
            async with asyncio.timeout(3.0):
                async with sse_client(self.mcp_url) as streams:
                    async with ClientSession(streams[0], streams[1]) as session:
                        await session.initialize()
                        result = await session.list_tools()
                        
                        for tool in result.tools:
                            async def call_mcp_tool(t_name=tool.name, **kwargs):
                                return await session.call_tool(t_name, arguments=kwargs)
                            
                            lc_tools.append(StructuredTool.from_function(
                                func=None,
                                coroutine=call_mcp_tool,
                                name=tool.name,
                                description=tool.description or "MCP Tool"
                            ))
                        logger.info(f"✅ Successfully loaded {len(lc_tools)} MCP tools")
                        return lc_tools
        except Exception as e:
            logger.warning(f"⚠️ Could not connect to MCP Server: {e}")
            return []
