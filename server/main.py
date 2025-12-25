import sys
import os
import uvicorn
import requests
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv, find_dotenv

# טעינת הטוקן
load_dotenv(find_dotenv())
HF_TOKEN = os.getenv("HF_TOKEN") # וודא שהוספת את זה ל-.env

# --- Path Setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import server.database as db

try:
    from ai_agent.agent_core import TravelAgent
    agent = TravelAgent()
    print("✅ AI Agent loaded successfully.")
except ImportError as e:
    agent = None
    print(f"⚠️ Warning: 'ai_agent' module not found. Error: {e}")

app = FastAPI(title="Smart Travel Agent API")

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

class RegisterRequest(BaseModel):
    username: str
    password: str

class TripRequest(BaseModel):
    username: str
    destination: str
    origin: str
    stops: Optional[str] = ""
    budget: int
    currency: str
    interest: str
    duration: int

# --- Endpoints ---

@app.post("/register")
async def register(req: RegisterRequest):
    success = db.create_user(req.username, req.password)
    if success:
        db.log_event("UserRegistered", {"username": req.username})
        return {"status": "success", "message": "User created successfully"}
    else:
        raise HTTPException(status_code=400, detail="Username already exists")

@app.post("/login")
async def login(req: LoginRequest):
    if db.verify_user(req.username, req.password):
        db.log_event("UserLogin", {"username": req.username})
        return {"status": "success", "username": req.username}
    else:
        db.log_event("LoginFailed", {"username": req.username})
        raise HTTPException(status_code=401, detail="Invalid username or password")

# --- Endpoint חדש: תמלול דיבור (Speech to Text) ---
@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    מקבל קובץ אודיו, שולח למודל Whisper של Hugging Face, ומחזיר טקסט.
    """
    # מודל Whisper המהיר (Turbo)
    API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo"
    
    headers = {}
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"
    
    try:
        print(f"🎤 Receiving audio file: {file.filename}...")
        audio_bytes = await file.read()
        
        # שליחה ל-Hugging Face
        response = requests.post(API_URL, headers=headers, data=audio_bytes)
        
        if response.status_code == 200:
            result = response.json()
            text = result.get("text", "")
            print(f"✅ Transcribed: '{text}'")
            return {"text": text}
        else:
            print(f"❌ HF Error {response.status_code}: {response.text}")
            return {"text": "", "error": "Transcription failed"}
            
    except Exception as e:
        print(f"❌ Server Error: {e}")
        return {"text": "", "error": str(e)}

@app.post("/generate_trip")
async def generate_trip(req: TripRequest):
    print(f"🚀 Request: {req.origin} -> {req.destination}")
    
    # משתמשים בטקסט שהגיע (בין אם הוקלד או הוקלט)
    detected_interest = req.interest.title()
    
    # --- אופציונלי: סיווג כוונות ---
    # אפשר להשאיר את זה או להוריד, תלוי בך.
    # כאן אני משאיר את זה פשוט: ה-AI יקבל את הטקסט (המוקלט או הכתוב) כמו שהוא.

    try:
        db.log_event("TripRequested", req.dict())

        if agent:
            response_data = agent.generate_response(
                destination=req.destination,
                origin=req.origin,
                stops=req.stops,
                duration=req.duration,
                budget=req.budget,
                currency=req.currency,
                interest=detected_interest
            )
            
            if "error" in response_data:
                raise HTTPException(status_code=500, detail=response_data["error"])
                
            trip_plan = response_data.get("trip_plan", {})
            
        else:
            trip_plan = {"summary": "Mock trip", "itinerary": []}

        trip_plan["detected_interest"] = detected_interest 
        result = {"trip_plan": trip_plan}

        db.log_event("TripGenerated", {
            "username": req.username, 
            "destination": req.destination,
            "trip_plan": trip_plan
        })
        
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