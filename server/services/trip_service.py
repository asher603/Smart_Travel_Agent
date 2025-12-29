import os
import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def get_llm():
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is missing!")
    return ChatGroq(temperature=0.7, model_name="llama-3.3-70b-versatile", api_key=GROQ_API_KEY)

def analyze_vibe(interest: str) -> str:
    try:
        llm = get_llm()
        msg = f"Analyze the following travel interest and return a ONE or TWO word category describing the vibe (e.g., 'Culinary', 'Adventure', 'Relaxing', 'Historical'). Interest: '{interest}'"
        response = llm.invoke([HumanMessage(content=msg)])
        return response.content.strip()
    except Exception as e:
        print(f"⚠️ Analysis Warning: {e}")
        return "General"

def normalize_trip_response(trip_data, req_dest="Trip", req_budget="?"):
    """מוודא שהמבנה אחיד ללקוח"""
    if "trip_plan" in trip_data:
        trip_data = trip_data["trip_plan"]
    
    return {
        "summary": trip_data.get("summary", "No summary available"),
        "analyzed_vibe": trip_data.get("analyzed_vibe", "General"),
        "itinerary": trip_data.get("itinerary", []),
        "destination": req_dest,
        "budget": req_budget
    }

def generate_trip_plan(req):
    print(f"🚀 Generating trip to {req.destination}...")
    vibe = analyze_vibe(req.interest)
    print(f"✨ Vibe Detected: {vibe}")

    prompt = f"""
    Create a detailed {req.duration}-day trip itinerary for {req.destination}.
    Budget: {req.budget} {req.currency}.
    Traveler Interest: {req.interest} (Vibe: {vibe}).
    
    Format the output strictly as JSON with this structure:
    {{
        "summary": "A brief exciting summary of the trip",
        "analyzed_vibe": "{vibe}",
        "itinerary": [
            {{
                "day": 1,
                "title": "Theme of the day",
                "activities": ["Activity 1", "Activity 2", "Restaurant recommendation"]
            }}
        ]
    }}
    Do NOT add any text outside the JSON.
    """

    try:
        llm = get_llm()
        response = llm.invoke([
            SystemMessage(content="You are an expert travel agent. You output only valid JSON."),
            HumanMessage(content=prompt)
        ])
        
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        raw_data = json.loads(content)
        # שימוש בנורמליזציה
        return normalize_trip_response(raw_data, req.destination, req.budget)

    except Exception as e:
        print(f"❌ Trip Generation Error: {e}")
        return {
            "summary": "Could not generate trip due to an error.",
            "analyzed_vibe": "Error",
            "itinerary": []
        }

def refine_trip_plan(current_plan, instruction):
    print(f"🛠️ Refining trip with instruction: {instruction}")
    
    prompt = f"""
    Current Trip Plan (JSON):
    {json.dumps(current_plan)}

    User Instruction: "{instruction}"

    Please modify the trip plan according to the instruction. 
    Keep the exact same JSON structure. Output ONLY JSON.
    Do NOT add any introductory text.
    """

    try:
        llm = get_llm()
        response = llm.invoke([
            SystemMessage(content="You are a JSON editing assistant. Output ONLY valid JSON."),
            HumanMessage(content=prompt)
        ])
        
        content = response.content.strip()
        # ניקוי המחרוזת (אותו לוגיקה כמו ב-Generate)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        parsed_json = json.loads(content)
        
        # נורמליזציה כדי להבטיח מבנה תקין
        # אנחנו מעבירים ערכים קיימים כי בעריכה הם לא משתנים לרוב
        final_plan = normalize_trip_response(parsed_json, current_plan.get("destination", ""), current_plan.get("budget", ""))
        
        return {"trip_plan": final_plan}
        
    except Exception as e:
        print(f"❌ Refine Error: {e}")
        return {"error": str(e)}