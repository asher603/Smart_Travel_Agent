import os
import json
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.tools import DuckDuckGoSearchRun
from fastapi import HTTPException 

# ---------------------------------------------------------
# ייבוא השירותים המיוחדים שלנו
# ---------------------------------------------------------
# 1. שירות האבטחה (בודק קלט זדוני)
from server.services.security_service import security_guard 
# 2. מנהל המודלים (מנגנון השרידות - Fallback)
from server.services.llm_factory import llm_manager 

load_dotenv()

def get_realtime_events(destination):
    """
    מבצע חיפוש באינטרנט אחר אירועים עכשווים ביעד (DuckDuckGo)
    """
    try:
        search = DuckDuckGoSearchRun()
        query = f"Tourist attractions, festivals, and events in {destination} right now"
        print(f"🕵️ Web Search: '{query}'...")
        results = search.run(query)
        # חותכים את התוצאה שלא תהיה ארוכה מדי
        return results[:1000] 
    except Exception as e:
        print(f"⚠️ Search failed: {e}")
        return "General tourist info."

def analyze_vibe(interest: str) -> str:
    """
    מנתח את סגנון הטיול באמצעות המודל
    """
    try:
        msg = f"Classify this travel interest into a short category (e.g., 'Culinary', 'Extreme', 'Relaxing', 'History'). Interest: '{interest}'"
        
        # שימוש במנגנון השרידות (Manager)
        response = llm_manager.invoke([HumanMessage(content=msg)])
        return response.content.strip()
    except Exception as e:
        print(f"⚠️ Analysis Warning: {e}")
        return "General"

def normalize_trip_response(trip_data, req_dest="Trip", req_budget="?"):
    """
    מנרמל את המבנה כדי שהקליינט לא יקרוס
    """
    if "trip_plan" in trip_data:
        trip_data = trip_data["trip_plan"]
    
    return {
        "summary": trip_data.get("summary", "A great trip awaits you!"),
        "analyzed_vibe": trip_data.get("analyzed_vibe", "General"),
        "itinerary": trip_data.get("itinerary", []),
        "destination": req_dest,
        "budget": req_budget
    }

def clean_json_response(content):
    """
    מנקה סימני Markdown מתשובת המודל
    """
    content = content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    return content

def generate_trip_plan(req):
    """
    הפונקציה הראשית: אבטחה -> חיפוש -> מנגנון שרידות (LLM) -> יצירה מפורטת
    """
    print(f"🚀 Generating DETAILED trip to {req.destination}...")

    # 1. 🛡️ בדיקת אבטחה
    # (הסרנו את travel_style כדי למנוע קריסה אם הוא לא קיים)
    user_inputs = [req.destination, req.interest]
    for text in user_inputs:
        if text and str(text).strip():
            security_check = security_guard.is_safe(str(text))
            if not security_check["safe"]:
                print(f"⛔ Blocked Input: {text}")
                raise HTTPException(
                    status_code=403, 
                    detail=f"Security Violation: {security_check['reason']}"
                )
    print("✅ Security Check Passed.")

    # 2. 🌍 חיפוש מידע בזמן אמת
    real_events_context = get_realtime_events(req.destination)

    # 3. ✨ ניתוח אווירה
    vibe = analyze_vibe(req.interest)
    print(f"✨ Vibe: {vibe}")

    # 4. 🧠 בניית הפרומפט המפורט והפשוט (Simple Language & Detailed)
    prompt = f"""
    Act as a friendly local tour guide. Plan a {req.duration}-day trip to {req.destination}.
    
    CLIENT DETAILS:
    - Budget: {req.budget} {req.currency}
    - Interests: {req.interest}
    - Vibe: {vibe}
    
    REAL-TIME CONTEXT:
    {real_events_context}
    
    INSTRUCTIONS:
    1. **Detailed Descriptions:** Do NOT just list places. For every activity, write a full sentence explaining WHAT it is and WHY it's fun.
    2. **Simple Language:** Use easy-to-read English. Write like you are talking to a friend.
    3. **Specifics:** Recommend specific dishes to eat at restaurants.
    
    OUTPUT FORMAT (Strict JSON):
    {{
        "summary": "A rich, engaging summary of the trip...",
        "analyzed_vibe": "{vibe}",
        "itinerary": [
            {{
                "day": 1,
                "title": "Arrival & Exploration",
                "activities": [
                    "Start your morning at [Place Name]. It is famous for [Reason] and you can see [Specific Thing].",
                    "For lunch, go to [Restaurant Name] and try the delicious [Dish Name].",
                    "In the afternoon, take a relaxing walk through [Park/Area] to enjoy the atmosphere."
                ]
            }}
        ]
    }}
    Response must be ONLY valid JSON.
    """

    try:
        # שימוש במנגנון השרידות (Fallback Manager)
        # הוא ינסה את Groq, ואם ייכשל - יעבור ל-HuggingFace
        response = llm_manager.invoke([
            SystemMessage(content="You are a helpful travel guide. Output strictly valid JSON."),
            HumanMessage(content=prompt)
        ])
        
        # ניקוי ופרסור
        json_content = clean_json_response(response.content)
        parsed_data = json.loads(json_content)
        
        return normalize_trip_response(parsed_data, req.destination, req.budget)

    except Exception as e:
        print(f"❌ Trip Generation Error: {e}")
        return {
            "summary": "We encountered an error while planning your trip. Please try again.",
            "analyzed_vibe": "Error",
            "itinerary": [],
            "destination": req.destination,
            "budget": req.budget
        }

def refine_trip_plan(current_plan, instruction):
    """
    תיקון ושיפור הטיול הקיים
    """
    print(f"🛠️ Refining trip: '{instruction}'")

    # 1. בדיקת אבטחה
    security_check = security_guard.is_safe(instruction)
    if not security_check["safe"]:
        return {"error": f"Security Violation: {security_check['reason']}"}

    prompt = f"""
    Current Itinerary (JSON):
    {json.dumps(current_plan)}

    User Request: "{instruction}"

    TASK:
    Update the JSON based on the request. 
    **IMPORTANT:** Keep the descriptions detailed and simple. Do not shorten them.
    Output ONLY the updated JSON.
    """

    try:
        # שימוש במנגנון השרידות
        response = llm_manager.invoke([
            SystemMessage(content="You are a JSON editing assistant."),
            HumanMessage(content=prompt)
        ])
        
        json_content = clean_json_response(response.content)
        parsed_data = json.loads(json_content)
        
        final_plan = normalize_trip_response(parsed_data, current_plan.get("destination"), current_plan.get("budget"))
        return {"trip_plan": final_plan}

    except Exception as e:
        print(f"❌ Refine Error: {e}")
        return {"error": "Failed to update trip. Please try again."}