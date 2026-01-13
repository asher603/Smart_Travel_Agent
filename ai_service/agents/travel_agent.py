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
            # שימוש בלקוח הרשמי של MCP לחיבור SSE
            async with sse_client(self.mcp_url) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()
                    
                    # קבלת רשימת הכלים
                    result = await session.list_tools()
                    
                    # המרה פשוטה לכלים של LangChain
                    for tool in result.tools:
                        # יצירת כלי עוטף שקורא ל-MCP
                        async def call_mcp_tool(t_name=tool.name, **kwargs):
                            return await session.call_tool(t_name, arguments=kwargs)
                        
                        lc_tools.append(StructuredTool.from_function(
                            func=None,
                            coroutine=call_mcp_tool,
                            name=tool.name,
                            description=tool.description or "MCP Tool"
                        ))
                        
                    logger.info(f"✅ Successfully loaded {len(lc_tools)} MCP tools: {[t.name for t in result.tools]}")
                    return lc_tools

        except Exception as e:
            # במקרה של שגיאה - אנחנו מדפיסים אותה אבל מחזירים רשימה ריקה
            # זה קריטי כדי שהשירות לא יקרוס!
            logger.warning(f"⚠️ Could not connect to MCP Server: {e}")
            return []

    async def plan_trip(self, req: TripRequest, analyzed_vibe: str) -> Dict[str, Any]:
        # 1. ניסיון לטעון כלים (עם הגנה מקריסה)
        # שים לב: בגלל המבנה של MCP, החיבור צריך להישאר פתוח בזמן הריצה.
        # לצורך הפשטות כרגע, נריץ ללא כלים אם החיבור מורכב, או נשתמש ב-LLM בלבד.
        
        # הערה: חיבור MCP מלא דורש ניהול Context מורכב.
        # כדי שהמערכת שלך תעבוד *עכשיו*, נשתמש בידע של ה-LLM בלבד בשלב הראשון.
        # זה יבטיח שהטיול ייווצר בהצלחה.
        
        llm = self.manager.get_llm()
        
        # 2. בניית הפרומפט
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
        
        # 3. הפעלה
        response = await llm.invoke(messages)
        content = response.content if hasattr(response, 'content') else str(response)
        
        try:
            result = parser.parse(content)
            result["analyzed_vibe"] = analyzed_vibe
            return result
        except Exception:
            return {"error": "Failed to parse itinerary", "raw": content}