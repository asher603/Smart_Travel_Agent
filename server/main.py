import sys
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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

class TripRequest(BaseModel):
    username: str
    destination: str
    budget: int
    interest: str
    days: int  # <--- Added Field

# --- Endpoints ---

@app.post("/login")
async def login(req: LoginRequest):
    db.log_event("UserLogin", {"username": req.username})
    return {"status": "success", "username": req.username}

@app.post("/generate_trip")
async def generate_trip(req: TripRequest):
    print(f"🚀 Request: {req.destination}, {req.days} days, Budget: ${req.budget}")

    try:
        # 1. Log Request
        db.log_event("TripRequested", req.dict())

        # 2. Build Prompt (Enforcing structure for UI parsing)
        prompt = (
            f"Plan a {req.days}-day trip to {req.destination}. "
            f"Budget: ${req.budget}. Interest: {req.interest}. "
            f"IMPORTANT: Use '**Day 1:**', '**Day 2:**' format for each day."
        )

        # 3. Call AI
        if agent:
            response_text = agent.generate_response(prompt)
            if isinstance(response_text, dict):
                itinerary = response_text.get('trip_plan', str(response_text))
            else:
                itinerary = str(response_text)
        else:
            # Mock Data if AI is off
            itinerary = ""
            for i in range(1, req.days + 1):
                itinerary += f"**Day {i}:** Explore {req.destination}.\n* Morning: Visit landmark.\n* Lunch: Local food.\n\n"

        # 4. Result
        result = {
            "destination": req.destination,
            "days": req.days,
            "budget": req.budget,
            "weather": "Sunny 25°C",  # You can hook up a real Weather API later
            "itinerary": itinerary,
            "username": req.username
        }

        # 5. Log Success
        db.log_event("TripGenerated", result)
        
        return result

    except Exception as e:
        db.log_event("ErrorOccurred", {"error": str(e), "dest": req.destination})
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{username}")
def get_user_history(username: str):
    return db.get_user_events(username)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)