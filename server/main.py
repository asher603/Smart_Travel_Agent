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

# --- Imports for Chat & Image ---
from huggingface_hub import InferenceClient
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

# טעינת סביבה
load_dotenv(find_dotenv())
HF_TOKEN = os.getenv("HF_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

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

class ChatRequest(BaseModel):
    question: str
    context: str

# --- Endpoints ---

@app.post("/register")
async def register(req: RegisterRequest):
    if db.create_user(req.username, req.password):
        return {"status": "success", "message": "User created successfully"}
    raise HTTPException(status_code=400, detail="Username already exists")

@app.post("/login")
async def login(req: LoginRequest):
    if db.verify_user(req.username, req.password):
        return {"status": "success", "username": req.username}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")

@app.post("/generate_trip")
async def generate_trip(req: TripRequest):
    print(f"🚀 Generating Trip: {req.destination}")
    detected_interest = req.interest.title()
    try:
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
        return {"trip_plan": trip_plan}

    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_image")
async def generate_image(req: ImageRequest):
    print(f"🎨 Generating Image: {req.destination}")
    image_prompt = f"travel poster of {req.destination}"
    if req.interest:
        image_prompt += f", {req.interest} theme"
    image_prompt += ", cinematic, 8k, vibrant."
    
    try:
        client = InferenceClient(api_key=HF_TOKEN)
        image = client.text_to_image(prompt=image_prompt, model="black-forest-labs/FLUX.1-schnell")
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return {"image_base64": img_str}
    except Exception as e:
        print(f"❌ Image Error: {e}")
        return {"image_base64": None}

@app.post("/ask_question")
async def ask_question(req: ChatRequest):
    """
    מקבל שאלה והקשר, ומחזיר תשובה טקסטואלית מהירה.
    """
    print(f"❓ Question: {req.question}")
    try:
        # --- תיקון: עדכון שם המודל לגרסה החדשה והנתמכת ---
        llm = ChatGroq(
            temperature=0.7, 
            model_name="llama-3.3-70b-versatile", # מודל עדכני
            api_key=GROQ_API_KEY
        )
        
        messages = [
            SystemMessage(content="You are a helpful travel assistant. Answer the user's question clearly and concisely based on the trip context provided."),
            HumanMessage(content=f"TRIP CONTEXT:\n{req.context}\n\nUSER QUESTION:\n{req.question}")
        ]
        
        response = llm.invoke(messages)
        return {"answer": response.content}
        
    except Exception as e:
        print(f"❌ Chat Error: {e}")
        # החזרת שגיאה מפורטת יותר כדי שתראה אותה בבועה אם משהו נכשל
        return {"answer": f"Sorry, I encountered an error: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)