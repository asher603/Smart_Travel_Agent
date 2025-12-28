from fastapi import HTTPException
import sys
import os
import json
from langchain_core.messages import HumanMessage, SystemMessage
from server.services.analysis_service import analyze_user_vibe

# טעינת הסוכן הראשי
try:
    from ai_agent.agent_core import TravelAgent
    agent = TravelAgent()
    print("✅ Agent loaded successfully in Trip Service")
except ImportError as e:
    print(f"⚠️ Warning: Could not load TravelAgent. {e}")
    agent = None

def generate_trip_plan(data):
    """
    יצירת טיול חדש מאפס
    """
    print(f"🚀 Trip Service: Generating plan for {data.destination}...")
    
    try:
        # שלב 1: ניתוח אווירה
        trip_vibe = analyze_user_vibe(data.interest)
        
        # שלב 2: הכנת הנתונים לסוכן
        enriched_interest = f"{data.interest} (AI Detected Style: {trip_vibe})"
        
        trip_plan = {}

        if agent:
            response_data = agent.generate_response(
                destination=data.destination,
                origin=data.origin,
                stops=data.stops,
                duration=data.duration,
                budget=data.budget,
                currency=data.currency,
                interest=enriched_interest 
            )
            
            if "error" in response_data:
                raise HTTPException(status_code=500, detail=response_data["error"])
            
            trip_plan = response_data.get("trip_plan", {})
        else:
            # Mock למקרה שהסוכן לא עובד
            trip_plan = {"summary": "Mock trip (Agent offline)", "itinerary": []}

        # שלב 3: הוספת תוצאות הניתוח
        trip_plan["analyzed_vibe"] = trip_vibe 
        
        return {"trip_plan": trip_plan}

    except Exception as e:
        print(f"❌ Trip Service Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def refine_trip_plan(current_plan, user_instruction):
    print(f"🛠️ Refining trip with instruction: {user_instruction}")
    
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not loaded")

    try:
        # פרומפט אגרסיבי יותר שמכריח את המודל להחזיר רק JSON
        prompt = f"""
        You are a JSON processing engine. NOT a chat assistant.
        Your task is to modify the TRIP JSON based on the User Request.

        INPUT JSON:
        {json.dumps(current_plan)}

        USER REQUEST:
        {user_instruction}

        RULES:
        1. Output ONLY the valid JSON object.
        2. NO introduction text (like "Here is the json").
        3. NO markdown formatting (don't write ```json).
        4. Maintain the exact same structure keys: "summary", "itinerary", "cost_breakdown".
        5. If the user asks for something impossible, make a best effort modification.
        
        START RESPONSE WITH {{ AND END WITH }}:
        """
        
        messages = [
            SystemMessage(content="You output only raw JSON. No markdown. No chatter."),
            HumanMessage(content=prompt)
        ]
        
        response = agent.llm.invoke(messages)
        content = response.content.strip()
        
        print(f"🤖 Raw AI Response: {content[:100]}...") # לוג לצורך בדיקה

        # --- ניקוי אגרסיבי של התשובה ---
        # לפעמים המודל בכל זאת כותב שטויות, אנחנו נחתוך הכל עד הסוגריים המסולסלים
        if "```json" in content:
            content = content.replace("```json", "").replace("```", "")
        
        # חיפוש הסוגריים הראשונים והאחרונים (כדי להעיף טקסט בהתחלה או בסוף)
        start_index = content.find("{")
        end_index = content.rfind("}")
        
        if start_index != -1 and end_index != -1:
            content = content[start_index : end_index + 1]

        # המרה ל-JSON
        new_plan = json.loads(content)
        
        # שמירת ה-Vibe המקורי
        if "analyzed_vibe" in current_plan and "analyzed_vibe" not in new_plan:
            new_plan["analyzed_vibe"] = current_plan["analyzed_vibe"]
            
        return {"trip_plan": new_plan}

    except json.JSONDecodeError:
        print("❌ Error: AI did not return valid JSON.")
        raise HTTPException(status_code=500, detail="AI failed to generate valid JSON format.")
    except Exception as e:
        print(f"❌ Refine Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))