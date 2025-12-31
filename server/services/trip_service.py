import os
import json
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_groq import ChatGroq
from fastapi import HTTPException 

# ייבוא השירותים
from server.services.security_service import security_guard 
from server.services.llm_factory import llm_manager # זה (Gemini) יהיה המוח המרכזי

load_dotenv()

# כלי החיפוש
search_tool = DuckDuckGoSearchRun()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- פונקציית עזר למודל המהיר (Groq) ---
def get_groq_fast_model():
    """מחזיר מודל מהיר למשימות קטנות (סיכום נתונים)"""
    if not GROQ_API_KEY:
        # אם אין מפתח גרוק, נשתמש במנהל הראשי כגיבוי
        return llm_manager
    return ChatGroq(
        temperature=0.5, 
        model_name="llama-3.3-70b-versatile", 
        api_key=GROQ_API_KEY
    )

# --- כלי עזר לחיפוש ---
def run_search(query):
    try:
        # print(f"🕵️ Searching: {query}...")
        return search_tool.run(query)[:1000] # לוקחים טקסט רלוונטי
    except Exception:
        return "Data unavailable."

# ---------------------------------------------------------
# ⚡ Specialist Agents (מופעלים ע"י Groq למהירות)
# ---------------------------------------------------------

def analyze_vibe(interest: str) -> str:
    """ניתוח מהיר של ה-Vibe"""
    try:
        llm = get_groq_fast_model()
        msg = f"Classify this travel interest into a ONE word category (e.g., 'Culinary', 'Extreme', 'Relaxing'). Interest: '{interest}'"
        response = llm.invoke([HumanMessage(content=msg)])
        return response.content.strip()
    except Exception:
        return "General"

def flight_agent(destination):
    """סוכן הטיסות (Groq)"""
    print("✈️ Flight Agent (Groq): Scanning skies...")
    search_data = run_search(f"Cheap flights from Tel Aviv to {destination} next month prices")
    
    prompt = f"""
    Based on this search data, summarize flight options from Tel Aviv to {destination}.
    Mention average price and airlines. Keep it very short (2 sentences).
    Data: {search_data}
    """
    llm = get_groq_fast_model()
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()

def hotel_agent(destination, budget, vibe):
    """סוכן המלונות (Groq)"""
    print("🏨 Hotel Agent (Groq): Finding beds...")
    search_data = run_search(f"Best {vibe} hotels in {destination} under {budget} reviews")
    
    prompt = f"""
    Recommend 2 hotels in {destination} that fit the vibe '{vibe}'.
    Summarize why they are good based on: {search_data}.
    Keep it short.
    """
    llm = get_groq_fast_model()
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()

def weather_agent(destination):
    """סוכן המזג אוויר (Groq)"""
    print("🌤️ Weather Agent (Groq): Checking forecast...")
    search_data = run_search(f"Weather in {destination} this month average temperature")
    
    prompt = f"""
    Summarize the typical weather in {destination} now based on: {search_data}.
    Mention clothing advice. Max 2 sentences.
    """
    llm = get_groq_fast_model()
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()

# ---------------------------------------------------------
# 💎 The Planner (מופעל ע"י Gemini לאינטליגנציה ופורמט)
# ---------------------------------------------------------

def planner_agent(req, vibe, context_data, feedback=None, current_plan=None):
    """
    המתכנן הראשי. משתמש ב-llm_manager (Gemini) כדי להבטיח JSON תקין ותיאורים עשירים.
    """
    
    # הנחיות קפדניות לפורמט מחרוזות בלבד
    format_instruction = """
    ⚠️ CRITICAL: The 'activities' list must contain STRINGS ONLY. 
    Example: ["Visit the Eiffel Tower to see the view.", "Eat lunch at Le Petit Bistro."]
    Do NOT use objects like {"time": "10:00", "desc": "..."}.
    """

    if not feedback:
        print("🎨 Planner Agent (Gemini): Synthesizing Master Plan...")
        prompt = f"""
        Act as an expert travel architect. Plan a {req.duration}-day trip to {req.destination}.
        
        CLIENT DETAILS:
        - Budget: {req.budget} {req.currency}
        - Interests: {req.interest}
        - Vibe: {vibe}
        
        🕵️ INTELLIGENCE REPORTS (Real Data):
        - ✈️ Flights: {context_data['flights']}
        - 🏨 Hotels: {context_data['hotels']}
        - 🌤️ Weather: {context_data['weather']}
        - 🎉 Events: {context_data['events']}
        
        INSTRUCTIONS:
        1. **Summary:** Write an engaging summary incorporating the flight/hotel info.
        2. **Itinerary:** Create a detailed day-by-day plan.
        3. **Descriptions:** For every activity string, explain WHAT it is and WHY it's fun.
        
        OUTPUT FORMAT (Strict JSON):
        {{
            "summary": "...",
            "analyzed_vibe": "{vibe}",
            "itinerary": [
                {{
                    "day": 1,
                    "title": "Theme",
                    "activities": ["Activity 1 details...", "Activity 2 details...", "Dinner recommendation..."]
                }}
            ]
        }}
        {format_instruction}
        """
    else:
        print("🎨 Planner Agent (Gemini): Refining Plan...")
        prompt = f"""
        You are the Planner. The Critic found issues.
        PREVIOUS JSON: {json.dumps(current_plan)}
        CRITIC FEEDBACK: "{feedback}"
        TASK: Fix the JSON based on feedback. Keep the structure exactly the same.
        {format_instruction}
        Output ONLY JSON.
        """

    # שימוש ב-llm_manager (שהוא Gemini 2.5)
    response = llm_manager.invoke([
        SystemMessage(content="You are a JSON travel architect. Output strictly valid JSON."),
        HumanMessage(content=prompt)
    ])
    
    return json.loads(clean_json_response(response.content))

# ---------------------------------------------------------
# 🧐 The Critic (מופעל ע"י Gemini לדיוק לוגי)
# ---------------------------------------------------------

def critic_agent(trip_plan, req):
    """
    המבקר. בודק היגיון ולוגיקה.
    """
    print("🧐 Critic Agent (Gemini): Auditing...")
    prompt = f"""
    Review this trip plan for {req.destination}.
    JSON: {json.dumps(trip_plan)}
    
    CHECKLIST:
    1. Are 'activities' lists of STRINGS? (If they are objects/dicts -> REJECT).
    2. Is the summary detailed?
    3. Does it mention specific places?
    
    Output: "APPROVED" or a short list of fixes.
    """
    response = llm_manager.invoke([HumanMessage(content=prompt)])
    return response.content.strip()

# ---------------------------------------------------------
# ⚙️ Orchestrator
# ---------------------------------------------------------

def generate_trip_plan(req):
    print(f"🚀 Starting Hybrid-AI Trip Generation for {req.destination}...")

    # 1. אבטחה
    if not security_guard.is_safe(req.destination)["safe"]:
        raise HTTPException(status_code=403, detail="Security Violation")

    # 2. שלב המודיעין (מקבילי - Groq)
    # סוכנים אלו רצים מהר מאוד
    vibe = analyze_vibe(req.interest)
    
    flights_info = flight_agent(req.destination)
    hotels_info = hotel_agent(req.destination, req.budget, vibe)
    weather_info = weather_agent(req.destination)
    events_info = run_search(f"Events festivals in {req.destination} right now")
    
    context_data = {
        "flights": flights_info,
        "hotels": hotels_info,
        "weather": weather_info,
        "events": events_info
    }

    # 3. שלב התכנון (A2A Loop - Gemini)
    current_plan = None
    max_retries = 2
    
    for attempt in range(max_retries + 1):
        try:
            if attempt == 0:
                current_plan = planner_agent(req, vibe, context_data)
            else:
                current_plan = planner_agent(req, vibe, context_data, feedback=critique, current_plan=current_plan)

            critique = critic_agent(current_plan, req)
            
            if "APPROVED" in critique.upper():
                print("✅ Hybrid-AI Success: Plan Approved!")
                break
            else:
                print(f"⚠️ Critique: {critique}")
                if attempt == max_retries:
                    print("✋ Max retries reached. Delivering best effort.")
        
        except Exception as e:
            print(f"❌ Error in loop: {e}")
            if current_plan: return normalize_trip_response(current_plan, req.destination, req.budget)
            return {"summary": "Error generating plan", "itinerary": []}

    return normalize_trip_response(current_plan, req.destination, req.budget)

# --- כלי עזר ---
def normalize_trip_response(trip_data, req_dest="Trip", req_budget="?"):
    if "trip_plan" in trip_data: trip_data = trip_data["trip_plan"]
    return {
        "summary": trip_data.get("summary", ""),
        "analyzed_vibe": trip_data.get("analyzed_vibe", "General"),
        "itinerary": trip_data.get("itinerary", []),
        "destination": req_dest,
        "budget": req_budget
    }

def clean_json_response(content):
    content = content.strip()
    if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content: content = content.split("```")[1].split("```")[0].strip()
    return content

def refine_trip_plan(current_plan, instruction):
    print(f"🛠️ Refining trip: '{instruction}'")
    prompt = f"""
    Current JSON: {json.dumps(current_plan)}
    Request: {instruction}
    Important: Keep 'activities' as a list of strings.
    Output ONLY JSON.
    """
    try:
        response = llm_manager.invoke([HumanMessage(content=prompt)])
        return {"trip_plan": normalize_trip_response(json.loads(clean_json_response(response.content)), current_plan.get("destination"))}
    except: return {"error": "Failed"}