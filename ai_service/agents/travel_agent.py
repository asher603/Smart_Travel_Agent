from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import HumanMessage
from ddgs import DDGS
from ai_service.core.llm_factory import llm_manager
from ai_service.schemas.api_models import TripRequest, ChatRequest, RefineRequest

class TravelAgent:
    def __init__(self):
        self.manager = llm_manager

    def _search_web(self, query):
        try:
            results = DDGS().text(query, max_results=3)
            return "\n".join([f"- {r['title']}: {r['body']}" for r in results]) if results else "No data."
        except: return "Search unavailable (Offline Mode)."

    async def plan_trip(self, req: TripRequest, analyzed_vibe: str):
        # 1. Web Search
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
        
        response_message = await self.manager.invoke(messages)
        parser = JsonOutputParser()
        result = parser.parse(response_message.content)
        result["analyzed_vibe"] = analyzed_vibe
        return result

    async def chat(self, req: ChatRequest):
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful travel assistant. Answer short and concise."),
            ("user", "Context of trip: {context}\n\nUser Question: {question}")
        ])
        messages = prompt.format_messages(context=req.context, question=req.question)
        response = await self.manager.invoke(messages)
        return {"answer": response.content}

    async def refine_trip(self, req: RefineRequest):
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a travel agent. Update the JSON trip plan based on user instructions. Output ONLY JSON."),
            ("user", """
             Current Plan: {current_plan}
             User Update Instructions: {instructions}
             
             Return the fully updated JSON structure (same format as before).
             """)
        ])
        messages = prompt.format_messages(current_plan=str(req.current_plan), instructions=req.instructions)
        response = await self.manager.invoke(messages)
        
        parser = JsonOutputParser()
        return parser.parse(response.content)