import logging
import asyncio
import re
import json
import ast
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from contextlib import AsyncExitStack
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
        self.mcp_url = "http://mcp-server:8000/sse"
        self._mcp_session = None
        self._mcp_exit_stack = None
        self._mcp_tools_cache = []
        self._mcp_lock = asyncio.Lock()

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
                "itinerary": [ ... ],
                "hotels": [
                    {{
                        "name": "Hotel Name",
                        "stars": 4,
                        "price_per_night": 120,
                        "neighborhood": "City Center",
                        "highlights": ["Free WiFi", "Pool"],
                        "why": "Short reason"
                    }}
                ],
                "packing_list": [
                    {{
                        "category": "Clothing",
                        "items": ["T-shirts x3", "Jeans x2"]
                    }}
                ]
             }}
             
             HOTEL RULES: Keep exactly 3 hotels (budget, mid-range, luxury). Use real hotel names.
             PACKING LIST RULES: Keep 5-7 categories with 3-6 items each. Tailor to destination, duration, interests, and gender.
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

            # --- n8n Automation for refined plan (Fire & Forget) ---
            if result and "itinerary" in result and req.email:
                # Build a minimal TripRequest-like object for _trigger_automation
                dest = req.current_plan.get("destination", "Unknown")
                origin = req.current_plan.get("origin", "Unknown")
                itinerary = result.get("itinerary", [])
                duration = len(itinerary) if itinerary else 5
                mock_req = TripRequest(
                    destination=dest,
                    origin=origin,
                    duration=duration,
                    budget=int(req.current_plan.get("budget", 2000)),
                    currency=req.current_plan.get("currency", "USD"),
                    interest=req.current_plan.get("interests", "General"),
                    email=req.email,
                    model=req.model
                )
                asyncio.create_task(self._trigger_automation(result, mock_req))

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

        # --- MCP Tool Enrichment (Real-time flight & weather data) ---
        start_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        enrichment = await self._get_mcp_enrichment(
            origin=sanitized["origin"],
            destination=sanitized["destination"],
            date=start_date
        )
        enrichment_text = ""
        if enrichment.get("flights"):
            enrichment_text += f"\n\nReal-time Flight Data (from MCP tools):\n{enrichment['flights']}"
        if enrichment.get("weather"):
            enrichment_text += f"\n\nCurrent Weather at Destination (from MCP tools):\n{enrichment['weather']}"

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
             Travelers gender: {gender}.
             {enrichment}
             
             IMPORTANT: Return ONLY valid JSON. No markdown formatting, no explanations.
             Use the real-time data above (if available) to make the plan more accurate.
             Structure:
             {{
                "summary": "...",
                "budget_breakdown": {{ "Flights": 0, "Accommodation": 0, "Food": 0, "Activities": 0, "Transport": 0 }},
                "itinerary": [ {{ "day": 1, "title": "...", "activities": ["..."] }} ],
                "hotels": [
                    {{
                        "name": "Hotel Name",
                        "stars": 4,
                        "price_per_night": 120,
                        "neighborhood": "City Center",
                        "highlights": ["Free WiFi", "Pool", "Near attractions"],
                        "why": "Short reason why this hotel fits the traveler's preferences"
                    }}
                ],
                "packing_list": [
                    {{
                        "category": "Clothing",
                        "items": ["T-shirts x3", "Jeans x2", "Jacket"]
                    }}
                ]
             }}
             
             HOTEL RULES:
             - Recommend exactly 3 hotels at different price tiers (budget, mid-range, luxury) that fit the total budget.
             - Hotels must be real, well-known hotels in the destination city.
             - Consider the traveler's interests and vibe when choosing hotels.
             - price_per_night should be a realistic integer in the trip currency.
             - stars should be 1-5.
             
             PACKING LIST RULES:
             - Create a practical packing list with 5-7 categories (e.g. Clothing, Toiletries, Electronics, Documents, Accessories, Health, Gear).
             - Each category should have 3-6 specific items.
             - Items MUST be tailored to: destination weather, trip duration, traveler interests, AND travelers gender ({gender}).
             - For gender-specific items, recommend appropriate clothing and toiletries.
             - If activities like hiking, beach, or sports are planned, include relevant gear.
             - Include travel documents and essentials.
             """)
        ])

        messages = prompt.format_messages(
            duration=req.duration, 
            origin=sanitized["origin"], 
            destination=sanitized["destination"],
            budget=req.budget, 
            currency=req.currency, 
            interest=prompt_guard.wrap_user_input(sanitized["interests"]),
            vibe=analyzed_vibe,
            enrichment=enrichment_text,
            gender=req.gender
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
        pattern = r"```(?:json|JSON)?\s*(.*?)\s*```"
        match = re.search(pattern, json_str, re.DOTALL)

        if match:
            return match.group(1).strip()
        
        start = json_str.find("{")
        end = json_str.rfind("}")
        if start != -1 and end != -1:
            return json_str[start : end + 1]
        
        return json_str

    async def _get_mcp_enrichment(self, origin: str, destination: str, date: str) -> Dict[str, Optional[str]]:
        """
        Connects to MCP server via SSE, discovers available tools dynamically,
        and invokes them to fetch real-time flight & weather data.
        Returns enrichment data dict to enhance the AI planning prompt.
        Gracefully degrades if MCP server is unavailable.
        """
        enrichment: Dict[str, Optional[str]] = {"flights": None, "weather": None}
        try:
            enrichment = await asyncio.wait_for(
                self._invoke_mcp_tools(origin, destination, date),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            logger.warning("⚠️ MCP Server connection timed out — proceeding without enrichment")
        except Exception as e:
            logger.warning(f"⚠️ MCP Server unavailable ({e}) — proceeding without enrichment")

        return enrichment

    async def _invoke_mcp_tools(self, origin: str, destination: str, date: str) -> Dict[str, Optional[str]]:
        """Internal helper: uses persistent MCP connection to call tools."""
        enrichment: Dict[str, Optional[str]] = {"flights": None, "weather": None}
        
        try:
            session, cached_tools = await asyncio.wait_for(self._get_mcp_session(), timeout=5.0)
            tool_names = [t.name for t in cached_tools]
        except Exception as e:
            logger.warning(f"⚠️ Could not establish MCP session: {e}")
            return enrichment

        try:
            # Invoke flight search if available
            if "search_flights" in tool_names:
                try:
                    flight_result = await session.call_tool(
                        "search_flights",
                        arguments={"origin": origin, "destination": destination, "date": date}
                    )
                    if flight_result.content:
                        enrichment["flights"] = str(flight_result.content[0].text)
                        logger.info("✈️ MCP flight data retrieved successfully")
                except Exception as e:
                    logger.warning(f"⚠️ MCP flight tool error: {e}")
                    await self._close_mcp_connection() # Trigger reconnect next time

            # Invoke weather tool if available
            if "get_weather" in tool_names:
                try:
                    weather_result = await session.call_tool(
                        "get_weather",
                        arguments={"city": destination}
                    )
                    if weather_result.content:
                        enrichment["weather"] = str(weather_result.content[0].text)
                        logger.info("🌤️ MCP weather data retrieved successfully")
                except Exception as e:
                    logger.warning(f"⚠️ MCP weather tool error: {e}")
                    await self._close_mcp_connection() # Trigger reconnect next time

        except Exception as e:
            logger.warning(f"⚠️ General MCP invocation error: {e}")
            await self._close_mcp_connection()

        return enrichment

    async def _fetch_mcp_tools(self) -> List[BaseTool]:
        """
        Connects to MCP server and wraps discovered tools as LangChain StructuredTools.
        Used for LangChain Agent Executor integration (tool-calling agents).
        """
        lc_tools = []
        try:
            return await asyncio.wait_for(self._fetch_mcp_tools_inner(), timeout=3.0)
        except asyncio.TimeoutError:
            logger.warning("⚠️ MCP tool fetch timed out")
            return []
        except Exception as e:
            logger.warning(f"⚠️ Could not connect to MCP Server: {e}")
            return []

    async def _fetch_mcp_tools_inner(self) -> List[BaseTool]:
        """Internal helper for _fetch_mcp_tools."""
        lc_tools = []
        try:
            session, cached_tools = await self._get_mcp_session()
            
            for tool in cached_tools:
                # IMPORTANT: Use default arguments in the lambda/closure to avoid late-binding issues
                async def call_mcp_tool(t_name=tool.name, **kwargs):
                    # Grab the current active session dynamically
                    current_session, _ = await self._get_mcp_session() 
                    return await current_session.call_tool(t_name, arguments=kwargs)
                
                lc_tools.append(StructuredTool.from_function(
                    func=None,
                    coroutine=call_mcp_tool,
                    name=tool.name,
                    description=tool.description or "MCP Tool"
                ))
            logger.info(f"✅ Successfully loaded {len(lc_tools)} MCP tools for LangChain")
            return lc_tools
        except Exception as e:
            logger.warning(f"⚠️ MCP tools inner error: {e}")
            await self._close_mcp_connection()
            return []
        
    async def _get_mcp_session(self):
        """Returns an active MCP session and cached tools, reconnecting if necessary."""
        async with self._mcp_lock:
            # Return existing session if it's already active
            if self._mcp_session:
                return self._mcp_session, self._mcp_tools_cache

            try:
                logger.info("🔌 Initializing persistent MCP connection...")
                self._mcp_exit_stack = AsyncExitStack()
                
                # Enter and hold the async contexts open
                streams = await self._mcp_exit_stack.enter_async_context(sse_client(self.mcp_url))
                self._mcp_session = await self._mcp_exit_stack.enter_async_context(ClientSession(streams[0], streams[1]))
                
                await self._mcp_session.initialize()
                
                # Cache the tools so we don't have to list them every time
                tools_result = await self._mcp_session.list_tools()
                self._mcp_tools_cache = tools_result.tools 
                
                logger.info(f"✅ MCP connected. Discovered tools: {[t.name for t in self._mcp_tools_cache]}")
                return self._mcp_session, self._mcp_tools_cache
                
            except Exception as e:
                logger.error(f"❌ Failed to connect to MCP: {e}")
                await self._close_mcp_connection()
                raise e

    async def _close_mcp_connection(self):
        """Closes the persistent MCP connection safely."""
        if self._mcp_exit_stack:
            try:
                await self._mcp_exit_stack.aclose()
            except Exception as e:
                logger.warning(f"⚠️ Error closing MCP connection: {e}")
                
        self._mcp_session = None
        self._mcp_exit_stack = None
        self._mcp_tools_cache = []
