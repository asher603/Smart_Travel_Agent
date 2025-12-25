import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from duckduckgo_search import DDGS

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class TravelAgent:
    def __init__(self):
        if not GROQ_API_KEY:
            print("❌ Error: Missing GROQ_API_KEY in .env")
            self.llm = None
            return

        # אתחול המודל דרך LangChain (דרישה 9 בהנחיות)
        try:
            self.llm = ChatGroq(
                temperature=0,
                model_name="llama-3.3-70b-versatile",
                api_key=GROQ_API_KEY
            )
            print("✅ LangChain Agent Initialized (Llama 3.3)")
        except Exception as e:
            print(f"❌ LangChain Init Error: {e}")
            self.llm = None

    def search_web(self, query):
        """חיפוש מידע משלים ברשת (טיסות/מחירים עדכניים)"""
        print(f"🔎 Searching: {query}...")
        try:
            results = DDGS().text(query, max_results=2)
            if not results: return "No specific data found."
            return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
        except Exception as e:
            print(f"Search warning: {e}")
            return "Search unavailable."

    def generate_response(self, destination, origin, stops, duration, budget, currency, interest):
        print(f"🤖 LangChain is planning trip to {destination} based on interest: {interest}...")
        
        if not self.llm:
            return {"error": "LLM not initialized"}

        # 1. איסוף מידע (RAG)
        flight_info = self.search_web(f"flights from {origin} to {destination} price")
        
        # 2. הגדרת הפרומפט
        # שים לב: אנחנו מזריקים את ה-interest (שיכול להיות קטגוריה מ-HF או טקסט חופשי)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert travel agent. You MUST output ONLY valid JSON."),
            ("user", """
             Plan a {duration}-day trip from {origin} to {destination}.
             Budget: {budget} {currency}.
             User Interest/Vibe: {interest} (Strictly tailor the trip to this vibe!).
             
             Real-time Flight Data: {flight_info}
             
             Return JSON with this exact structure:
             {{
                "summary": "A short summary of the trip highlighting the selected vibe",
                "budget_breakdown": {{ "Flights": int, "Accommodation": int, "Food": int, "Activities": int, "Transport": int }},
                "itinerary": [ 
                    {{ "day": 1, "title": "Day Title", "activities": ["Activity 1", "Activity 2"] }} 
                ]
             }}
             """)
        ])

        # 3. הרצת השרשרת (Chain)
        try:
            chain = prompt | self.llm | JsonOutputParser()
            
            response_data = chain.invoke({
                "duration": duration,
                "origin": origin,
                "destination": destination,
                "budget": budget,
                "currency": currency,
                "interest": interest,
                "flight_info": flight_info
            })
            
            return {"trip_plan": response_data}

        except Exception as e:
            print(f"LangChain Error: {e}")
            return {"error": str(e), "trip_plan": {}}