import os
import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

# נשתמש באותו מפתח API שכבר מוגדר אצלך
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def get_llm():
    """מחזיר מופע של המודל לשימוש חוזר"""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is missing!")
    return ChatGroq(temperature=0.7, model_name="llama-3.3-70b-versatile", api_key=GROQ_API_KEY)

def analyze_vibe(interest: str) -> str:
    """מנתח את סגנון הטיול על סמך תחומי העניין"""
    try:
        llm = get_llm()
        msg = f"Analyze the following travel interest and return a ONE or TWO word category describing the vibe (e.g., 'Culinary', 'Adventure', 'Relaxing', 'Historical'). Interest: '{interest}'"
        response = llm.invoke([HumanMessage(content=msg)])
        return response.content.strip()
    except Exception as e:
        print(f"⚠️ Analysis Warning: {e}")
        return "General"

def generate_trip_plan(req):
    """מייצר את מסלול הטיול המלא"""
    print(f"🚀 Generating trip to {req.destination}...")
    
    # 1. ניתוח וייב (עם טיפול בשגיאות)
    vibe = analyze_vibe(req.interest)
    print(f"✨ Vibe Detected: {vibe}")

    # 2. בניית הפרומפט
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
            }},
            ...
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
        
        # ניקוי ופירסור ה-JSON
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        trip_data = json.loads(content)
        return trip_data

    except Exception as e:
        print(f"❌ Trip Generation Error: {e}")
        return {
            "summary": "Could not generate trip due to an error.",
            "analyzed_vibe": "Error",
            "itinerary": []
        }

def refine_trip_plan(current_plan, instruction):
    """עריכת טיול קיים"""
    print(f"🛠️ Refining trip with instruction: {instruction}")
    
    prompt = f"""
    Current Trip Plan (JSON):
    {json.dumps(current_plan)}

    User Instruction: "{instruction}"

    Please modify the trip plan according to the instruction. 
    Keep the exact same JSON structure. Output ONLY JSON.
    """

    try:
        llm = get_llm()
        response = llm.invoke([
            SystemMessage(content="You are a JSON editing assistant."),
            HumanMessage(content=prompt)
        ])
        
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        
        return {"trip_plan": json.loads(content)}
        
    except Exception as e:
        return {"error": str(e)}