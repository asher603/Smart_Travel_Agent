import sys
import os
import uvicorn
import base64
from io import BytesIO
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv, find_dotenv

# --- הייבוא החדש והחשוב ---
from huggingface_hub import InferenceClient

# טעינת הטוקן
load_dotenv(find_dotenv())
HF_TOKEN = os.getenv("HF_TOKEN")

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

class ImageRequest(BaseModel):
    destination: str
    interest: str

# --- Endpoints ---

@app.post("/register")
async def register(req: RegisterRequest):
    if db.create_user(req.username, req.password):
        db.log_event("UserRegistered", {"username": req.username})
        return {"status": "success", "message": "User created successfully"}
    raise HTTPException(status_code=400, detail="Username already exists")

@app.post("/login")
async def login(req: LoginRequest):
    if db.verify_user(req.username, req.password):
        db.log_event("UserLogin", {"username": req.username})
        return {"status": "success", "username": req.username}
    else:
        db.log_event("LoginFailed", {"username": req.username})
        raise HTTPException(status_code=401, detail="Invalid username or password")

@app.post("/generate_trip")
async def generate_trip(req: TripRequest):
    print(f"🚀 Generating Trip: {req.origin} -> {req.destination}")
    
    detected_interest = req.interest.title()

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

@app.post("/generate_image")
async def generate_image(req: ImageRequest):
    """
    יצירת תמונה באמצעות המודל החדש FLUX.1-schnell והספרייה הרשמית.
    """
    print(f"🎨 Generating Image for: {req.destination} ({req.interest})")
    
    # Prompt קצר ומדויק יותר ל-FLUX
    image_prompt = f"travel poster of {req.destination}"
    if req.interest:
        image_prompt += f", {req.interest} theme"
    image_prompt += ", cinematic, 8k, vibrant."
    
    try:
        # --- השיטה החדשה והרשמית לפי התיעוד ---
        client = InferenceClient(api_key=HF_TOKEN)
        
        # קריאה למודל FLUX דרך ה-Client
        # זה מחזיר אובייקט תמונה של PIL (Python Imaging Library)
        image = client.text_to_image(
            prompt=image_prompt,
            model="black-forest-labs/FLUX.1-schnell"
        )
        
        # המרה מ-PIL Image ל-Base64 String כדי לשלוח ללקוח
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        print("✅ Image generated successfully via FLUX!")
        return {"image_base64": img_str}

    except Exception as e:
        print(f"❌ HF Inference Error: {e}")
        # במקרה חירום: נסה מודל גיבוי קל יותר אם FLUX עמוס
        return {"image_base64": None}

@app.get("/history/{username}")
def get_user_history(username: str):
    return db.get_user_events(username)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)