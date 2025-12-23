import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from duckduckgo_search import DDGS

# טעינת המפתח
load_dotenv()
# וודא שבקובץ .env שמת: GROQ_API_KEY=gsk_...
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    # גיבוי למקרה ששכחת לשנות את השם ב-.env
    GROQ_API_KEY = os.getenv("GOOGLE_API_KEY") 

if not GROQ_API_KEY or not GROQ_API_KEY.startswith("gsk_"):
    print("❌ Error: Missing Valid Groq API Key (starts with 'gsk_')")
    # אל תעצור, תן לו ליפול יפה בהמשך אם צריך
    
class TravelAgent:
    def __init__(self):
        # חיבור לשרתים של Groq באמצעות הספרייה של OpenAI
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=GROQ_API_KEY
        )
        # המודל הכי חזק וחינמי של Groq
        self.model_name = "llama-3.3-70b-versatile"
        
        print(f"✅ Agent Initialized on Groq (Llama 3.3): {self.model_name}")

    def search_web(self, query):
        """חיפוש עצמאי ומהיר"""
        print(f"🔎 Llama is searching for: {query}...")
        try:
            # שימוש ב-DuckDuckGo ללא תלות ב-API חיצוני
            results = DDGS().text(query, max_results=3)
            if not results: return "No data found."
            return "\n".join([f"- {r['title']}: {r['body']}" for r in results])
        except Exception as e:
            print(f"Search Error: {e}")
            return "Search failed."

    def generate_response(self, destination, origin, stops, duration, budget, currency, interest):
        print(f"🤖 Llama 3.3 is planning trip to {destination}...")

        # 1. הבאת מידע מהאינטרנט (RAG)
        flight_info = self.search_web(f"flights from {origin} to {destination} price {currency}")
        hotel_info = self.search_web(f"hotels in {destination} under {budget} {currency}")
        activity_info = self.search_web(f"top {interest} things to do in {destination}")

        # 2. הרכבת הפרומפט
        prompt = f"""
        Act as an expert travel agent. Plan a {duration}-day trip from {origin} to {destination}.
        
        **Constraints:**
        - Budget: {budget} {currency}
        - Interest: {interest}
        - Stops: {stops}

        **Real-Time Data (Use this for accuracy):**
        - Flights: {flight_info}
        - Hotels: {hotel_info}
        - Activities: {activity_info}

        **Instructions:**
        1. Build a detailed itinerary.
        2. Output ONLY valid JSON.
        
        **JSON Structure:**
        {{
            "summary": "Trip summary...",
            "budget_breakdown": {{
                "Flights": int, "Accommodation": int, "Food": int, "Activities": int, "Transport": int
            }},
            "itinerary": [
                {{ "day": 1, "title": "...", "activities": ["Morning...", "Afternoon...", "Evening..."] }}
            ]
        }}
        """

        try:
            # שליחה ל-Groq עם בקשה ל-JSON
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful travel assistant that outputs JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"} # מבטיח JSON תקין
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            return {"trip_plan": data}

        except Exception as e:
            print(f"Groq Error: {e}")
            return {
                "trip_plan": {
                    "summary": f"Error: {str(e)}",
                    "budget_breakdown": {"Error": 100},
                    "itinerary": []
                },
                "error": str(e)
            }