import logging
import asyncio
import re
import json
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
from ai_service.schemas.api_models import TripRequest

logger = logging.getLogger("uvicorn")

class TravelAgent:
    def __init__(self):
        self.manager = llm_manager
        # כתובת ה-MCP בתוך הדוקר
        self.mcp_url = "http://mcp-server:8000/sse"

    def _clean_json_string(self, json_str: str) -> str:
        """
        מנקה את המחרוזת מסימני Markdown כמו ```json
        כדי למנוע קריסות של הפארסר.
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

    async def plan_trip(self, req: TripRequest, analyzed_vibe: str) -> Dict[str, Any]:
        # 1. הכנת הפרומפט
        parser = JsonOutputParser()
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert travel agent. Create a detailed itinerary. OUTPUT MUST BE RAW JSON ONLY."),
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
            origin=req.origin, 
            destination=req.destination,
            budget=req.budget, 
            currency=req.currency, 
            interest=req.interest,
            vibe=analyzed_vibe
        )
        
        try:
            response = await self.manager.invoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # ניקוי ה-JSON לפני הפארסר
            cleaned_content = self._clean_json_string(content)
            
            try:
                result = parser.parse(cleaned_content)
            except Exception:
                logger.warning(f"⚠️ Standard parsing failed, attempting raw json load.")
                result = json.loads(cleaned_content)

            result["analyzed_vibe"] = analyzed_vibe

            # --- הפעלת האוטומציה (n8n) ---
            # אנחנו מפעילים את זה ברקע (Fire and Forget) כדי לא לעכב את התשובה למשתמש
            if result and "itinerary" in result:
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

    async def _trigger_automation(self, trip_data: dict, req: TripRequest):
        """שולח את פרטי הטיול ל-n8n בצורה שקטה"""
        print(f"DEBUG: Attempting to send data to n8n at {settings.N8N_WEBHOOK_URL}")
        try:
            # חישוב תאריכים דינמי (מתחילים מהיום)
            start_date_obj = datetime.now()
            end_date_obj = start_date_obj + timedelta(days=req.duration)
            
            # שליפת המייל (אם קיים בבקשה, אחרת דיפולטיבי)
            # אם תוסיף שדה email ל-TripRequest בעתיד, שנה את זה ל-req.email
            user_email = req.email if req.email else "user@example.com"
            payload = {
                "email": user_email,
                "summary": f"Trip to {req.destination}: {trip_data.get('summary', '')[:200]}...", # תקציר למייל
                "full_itinerary": str(trip_data.get("itinerary", [])), # המידע המלא
                "start_date": start_date_obj.strftime("%Y-%m-%d"),
                "end_date": end_date_obj.strftime("%Y-%m-%d")
            }
            
            async with httpx.AsyncClient() as client:
                # Timeout קצר כדי לא להיתקע אם n8n למטה
                resp = await client.post(settings.N8N_WEBHOOK_URL, json=payload, timeout=3.0)
                print(f"DEBUG: n8n response status: {resp.status_code}")
                
        except Exception as e:
            print(f"ERROR sending to n8n: {e}")