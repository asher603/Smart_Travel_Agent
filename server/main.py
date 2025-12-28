import sys
import os

# --- תיקון נתיבים ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

import server.database as db
from server.services import auth_service, trip_service, image_service

load_dotenv()

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

# --- מודלים ---
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

# מודל חדש לעריכה
class RefineRequest(BaseModel):
    current_plan: dict
    instruction: str

# --- Endpoints ---

@app.post("/register")
async def register(req: RegisterRequest):
    return auth_service.register_user(req)

@app.post("/login")
async def login(req: LoginRequest):
    return auth_service.login_user(req)

@app.post("/generate_trip")
async def generate_trip(req: TripRequest):
    db.log_event("TripGenerated", req.dict())
    return trip_service.generate_trip_plan(req)

# Endpoint חדש לעריכה
@app.post("/refine_trip")
async def refine_trip(req: RefineRequest):
    return trip_service.refine_trip_plan(req.current_plan, req.instruction)

@app.post("/generate_image")
async def generate_image(req: ImageRequest):
    return image_service.generate_trip_image(req.destination, req.interest)

# --- Chat ---
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

@app.post("/ask_question")
async def ask_question(req: ChatRequest):
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return {"answer": "Error: GROQ_API_KEY missing"}

        llm = ChatGroq(temperature=0.7, model_name="llama-3.3-70b-versatile", api_key=api_key)
        messages = [
            SystemMessage(content="You are a helpful travel assistant."),
            HumanMessage(content=f"CONTEXT:\n{req.context}\n\nQUESTION:\n{req.question}")
        ]
        response = llm.invoke(messages)
        return {"answer": response.content}
    except Exception as e:
        return {"answer": f"Error: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)