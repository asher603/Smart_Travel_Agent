from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import re

class TravelAgent:
    def __init__(self):
        # שימוש במודל החזק יותר
        self.llm = Ollama(model="llama3.2")

        # --- פרומפט מפלצתי ---
        # דורש פירוט לפי זמני היום והמלצות ספציפיות
        self.prompt = PromptTemplate(
            template="""
            You are a world-class luxury travel planner.
            Create a HIGHLY DETAILED, day-by-day itinerary for a trip.
            
            **TRIP DETAILS:**
            - Origin: {origin}
            - Destination: {destination}
            - Duration: {duration} days
            - Budget: {budget} {currency} (Total)
            - Stops: {stops}
            - Primary Interest: {interest}

            **REQUIREMENTS:**
            1. The itinerary must be EXTREMELY DETAILED. Do not just list places; describe the experience.
            2. Break down each day into "Morning", "Afternoon", and "Evening".
            3. Suggest specific, well-known restaurants, landmarks, or hidden gems related to the interest ({interest}).
            4. Include the flight route in the summary.
            5. The budget breakdown must be realistic percentages (integers).

            **OUTPUT FORMAT (STRICT JSON ONLY):**
            {{
                "summary": "A detailed 3-sentence summary of the flight path ({origin} -> {stops} -> {destination}) and the overall vibe of the trip, focusing on {interest}.",
                "budget_breakdown": {{
                    "Flights": 40,
                    "Accommodation": 25,
                    "Food & Dining": 20,
                    "Activities & Tours": 10,
                    "Transport (Local)": 5
                }},
                "itinerary": [
                    {{
                        "day": 1,
                        "title": "Arrival and First Impressions in {destination}",
                        "activities": [
                            "Morning: Land at airport, private transfer to hotel. Check-in and freshen up.",
                            "Afternoon: Introductory walking tour of the city center, visiting [Landmark 1] and [Landmark 2].",
                            "Evening: Welcome dinner at [Specific Restaurant Name] known for authentic local cuisine."
                        ]
                    }},
                    {{
                        "day": 2,
                        "title": "Deep Dive into {interest}",
                        "activities": [
                            "Morning: Visit [Specific Museum/Site] related to {interest}. Spend 3 hours exploring.",
                            "Afternoon: Lunch at a popular food market. Continue to [Another Site].",
                            "Evening: Enjoy a cultural performance or a sunset view from [Viewpoint]."
                        ]
                    }},
                    ... (REPEAT THIS STRUCTURE FOR EXACTLY {duration} DAYS)
                ]
            }}
            
            **CRITICAL:** Ensure the output is ONLY valid JSON. No introduction text. No explanation text at the end.
            """,
            input_variables=["destination", "origin", "stops", "duration", "budget", "currency", "interest"]
        )

        self.chain = self.prompt | self.llm | StrOutputParser()

    def generate_response(self, destination, origin, stops, duration, budget, currency, interest):
        try:
            print(f"AI: Thinking about {destination} for {duration} days ({interest})...")
            
            response_text = self.chain.invoke({
                "destination": destination,
                "origin": origin,
                "stops": stops if stops else "None (Direct)",
                "duration": str(duration),
                "budget": str(budget),
                "currency": currency,
                "interest": interest
            })
            
            # --- ניקוי JSON אגרסיבי ---
            # מחפש את הסוגריים המסולסלים החיצוניים ביותר
            match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if match:
                clean_json = match.group(0)
            else:
                raise ValueError("AI did not return valid JSON structure.")

            # המרה למילון
            data = json.loads(clean_json)
            
            # וידוא שתמיד יש תקציר
            if "summary" not in data or not data["summary"]:
                data["summary"] = f"A {duration}-day trip to {destination} focusing on {interest}. Enjoy!"

            return {"trip_plan": data}

        except Exception as e:
            print(f"AI Error: {e}")
            # במקרה חירום, מחזירים תשובה גנרית כדי שהלקוח לא יקרוס
            return {
                "trip_plan": {
                    "summary": "Sorry, I couldn't generate a detailed plan right now. Please try again.",
                    "budget_breakdown": {"Total": 100},
                    "itinerary": []
                }
            }