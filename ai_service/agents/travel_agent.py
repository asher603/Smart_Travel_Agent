import logging
import asyncio
import re
import json
from typing import List, Dict, Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import BaseTool, StructuredTool

# ייבוא הספריות הרשמיות של MCP
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
import httpx

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
        # ניקוי Markdown code blocks
        pattern = r"```json(.*?)```"
        match = re.search(pattern, json_str, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
        else:
            # ניסיון למצוא את ה-JSON בין סוגריים מסולסלים אם אין Markdown
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
            # הוספת Timeout כדי לא לתקוע את המערכת
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
            
            # --- תיקון 1: ניקוי ה-JSON לפני הפארסר ---
            cleaned_content = self._clean_json_string(content)
            
            try:
                # ניסיון ראשון עם הפארסר של LangChain
                result = parser.parse(cleaned_content)
            except Exception:
                # Fallback: שימוש ב-json רגיל אם LangChain נכשל
                logger.warning(f"⚠️ Standard parsing failed, attempting raw json load. Content snippet: {cleaned_content[:50]}...")
                result = json.loads(cleaned_content)

            result["analyzed_vibe"] = analyzed_vibe
            return result
            
        except Exception as e:
            logger.error(f"❌ AI Execution Failed: {e}")
            # החזרת תשובה בסיסית במקרה של כישלון מוחלט כדי שהקליינט לא יקרוס
            return {
                "summary": f"AI generation failed due to error: {str(e)}. Please try again.",
                "itinerary": [],
                "budget_breakdown": {},
                "analyzed_vibe": "Error"
            }