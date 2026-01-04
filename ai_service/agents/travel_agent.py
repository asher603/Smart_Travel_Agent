from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import HumanMessage
from duckduckgo_search import DDGS
from ai_service.core.llm_factory import llm_manager
from ai_service.schemas.api_models import TripRequest

class TravelAgent:
    def __init__(self):
        # Use our Factory which wraps the settings logic
        # We use 'invoke' method of the manager which handles fallback logic
        self.manager = llm_manager

    def _search_web(self, query):
        try:
            results = DDGS().text(query, max_results=3)
            return "\n".join([f"- {r['title']}: {r['body']}" for r in results]) if results else "No data."
        except: return "Search unavailable."

    async def plan_trip(self, req: TripRequest, analyzed_vibe: str):
        # 1. RAG
        flight_info = self._search_web(f"flights from {req.origin} to {req.destination} price {req.currency}")

        # 2. Prompt
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

        # 3. Execution (Using the Factory's LLM)
        # We need the actual LLM object for the chain, or we wrap the chain execution.
        # For simplicity with LangChain chains, we get the primary model object from the factory.
        llm = self.manager._get_primary_model()
        
        chain = prompt | llm | JsonOutputParser()
        
        result = await chain.ainvoke({
            "duration": req.duration, "origin": req.origin, "destination": req.destination,
            "budget": req.budget, "currency": req.currency, "interest": req.interest,
            "vibe": analyzed_vibe, "flight_info": flight_info
        })
        
        result["analyzed_vibe"] = analyzed_vibe
        return result