import logging
import asyncio
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

    async def _fetch_mcp_tools(self) -> List[BaseTool]:
        """
        Connects to MCP server manually using the official SDK.
        """
        lc_tools = []
        try:
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
            ("system", "You are an expert travel agent. Create a detailed itinerary."),
            ("user", """
             Plan a {duration}-day trip from {origin} to {destination}.
             Budget: {budget} {currency}.
             Interests: {interest}.
             Vibe: {vibe}.
             
             Return a valid JSON with an 'itinerary' list.
             {format_instructions}
             """)
        ])

        messages = prompt.format_messages(
            duration=req.duration, 
            origin=req.origin, 
            destination=req.destination,
            budget=req.budget, 
            currency=req.currency, 
            interest=req.interest,
            vibe=analyzed_vibe,
            format_instructions=parser.get_format_instructions()
        )
        
        # 2. הפעלה - התיקון הגדול כאן!
        # במקום: await llm.invoke (שגורם לקריסה כי invoke הוא סינכרוני)
        # אנחנו משתמשים במנהל שבנית שיודע לעבוד אסינכרונית וגם יש לו גיבויים
        try:
            response = await self.manager.invoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
            
            result = parser.parse(content)
            result["analyzed_vibe"] = analyzed_vibe
            return result
            
        except Exception as e:
            logger.error(f"❌ AI Execution Failed: {e}")
            # החזרת תשובה בסיסית במקרה של כישלון מוחלט כדי שהקליינט לא יקרוס
            return {
                "summary": "AI generation failed, please try again.",
                "itinerary": [],
                "budget_breakdown": {},
                "analyzed_vibe": "Error"
            }