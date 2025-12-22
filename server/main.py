import sys
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# --- Path Setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import Database
import server.database as db

# Try importing the AI agent
try:
    from ai_agent.agent_core import TravelAgent
    agent = TravelAgent()
    print("✅ AI Agent loaded successfully.")
except ImportError:
    agent = None
    print("⚠️ Warning: 'ai_agent' module not found. Using Mock mode.")

app = FastAPI(title="Smart Travel Agent API")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_db_client():
    db.init_db()

# --- Models ---
class LoginRequest(BaseModel):
    username: str
    password: str

# המודל המעודכן - תואם לדשבורד החדש
class TripRequest(BaseModel):
    username: str
    destination: str
    origin: str          # <--- חדש
    stops: Optional[str] = "" # <--- חדש (אופציונלי)
    budget: int
    currency: str        # <--- חדש
    interest: str
    duration: int        # שיניתי ל-duration כדי שיהיה אחיד, שים לב שבקוד הישן זה היה days

# --- Endpoints ---

@app.post("/login")
async def login(req: LoginRequest):
    db.log_event("UserLogin", {"username": req.username})
    return {"status": "success", "username": req.username}

@app.post("/generate_trip")
async def generate_trip(req: TripRequest):
    print(f"🚀 Request: {req.origin} -> {req.destination} ({req.duration} days)")

    try:
        # 1. Log Request
        db.log_event("TripRequested", req.dict())

        # 2. Call AI Agent
        if agent:
            # אנו שולחים את המשתנים הנפרדים ל-AI, והוא בונה את הפרומפט
            response_data = agent.generate_response(
                destination=req.destination,
                origin=req.origin,
                stops=req.stops,
                duration=req.duration,
                budget=req.budget,
                currency=req.currency,
                interest=req.interest
            )
            
            # אם ה-AI החזיר שגיאה פנימית
            if "error" in response_data:
                raise HTTPException(status_code=500, detail=response_data["error"])
                
            trip_plan = response_data.get("trip_plan", {})
            
        else:
            # Mock Data (גיבוי למקרה שה-AI לא עובד)
            trip_plan = {
                "summary": "Mock trip summary.", 
                "budget_breakdown": {"Food": 50, "Hotel": 50},
                "itinerary": []
            }

        # 3. Result Structure
        result = {
            "trip_plan": trip_plan # הלקוח מצפה לזה במבנה הזה
        }

        # 4. Log Success
        db.log_event("TripGenerated", {"user": req.username, "dest": req.destination})
        
        return result

    except Exception as e:
        db.log_event("ErrorOccurred", {"error": str(e)})
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{username}")
def get_user_history(username: str):
    return db.get_user_events(username)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)