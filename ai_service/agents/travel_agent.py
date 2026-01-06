from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import HumanMessage
from duckduckgo_search import DDGS
from ai_service.core.llm_factory import llm_manager
from ai_service.schemas.api_models import TripRequest

class TravelAgent:
    def __init__(self):
        self.manager = llm_manager

    def _search_web(self, query):
        try:
            results = DDGS().text(query, max_results=3)
            return "\n".join([f"- {r['title']}: {r['body']}" for r in results]) if results else "No data."
        except: return "Search unavailable (Offline Mode)."

    async def plan_trip(self, req: TripRequest, analyzed_vibe: str):
        # 1. Web Search (Will gracefully fail if offline)
        flight_info = self._search_web(f"flights from {req.origin} to {req.destination} price {req.currency}")

        # 2. Define Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert travel agent. Output valid JSON only."),
            ("user", """
             Plan a {duration}-day trip from {origin} to {destination}.
             Budget: {budget} {currency}.
             User Interest: "{interest}".
             Analyzed Vibe: {vibe} (Tailor the trip to this!).
             
             Real-time Flight Data: {flight_info}
             
             Return JSON:
             {{
                "summary": "Short summary...",
                "budget_breakdown": {{ "Flights": int, "Accommodation": int, "Food": int, "Activities": int, "Transport": int }},
                "itinerary": [ {{ "day": 1, "title": "...", "activities": ["..."] }} ]
             }}
             """)
        ])

        # 3. Execution with Fallback Strategy
        # במקום לבנות שרשרת עם מודל בודד, אנחנו מפרמטים את ההודעות
        # ושולחים אותן ל-Manager שיודע לנסות את כל המודלים לפי הסדר
        
        messages = prompt.format_messages(
            duration=req.duration, 
            origin=req.origin, 
            destination=req.destination,
            budget=req.budget, 
            currency=req.currency, 
            interest=req.interest,
            vibe=analyzed_vibe, 
            flight_info=flight_info
        )
        
        # כאן קורה הקסם: אם גוגל נכשל, ה-Manager יעבור אוטומטית ל-Groq ואז ל-Ollama
        response_message = await self.manager.invoke(messages)
        
        # 4. Parse the result
        parser = JsonOutputParser()
        result = parser.parse(response_message.content)
        
        result["analyzed_vibe"] = analyzed_vibe
        return result