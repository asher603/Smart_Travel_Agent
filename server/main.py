import sys
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv, find_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import server.database as db
from server.services import auth_service, trip_service, image_service
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv(find_dotenv())

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

# Models
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
    budget: int
    currency: str
    interest: str
    duration: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    stops: Optional[str] = ""

class TripUpdateRequest(BaseModel):
    trip_id: str
    chat_history: List[Dict[str, Any]]

class HistoryRequest(BaseModel):
    username: str

class GetTripRequest(BaseModel):
    trip_id: str

class DeleteTripRequest(BaseModel):
    trip_id: str

class ImageRequest(BaseModel):
    destination: str
    interest: str

class RefineRequest(BaseModel):
    current_plan: dict
    instruction: str

class ChatRequest(BaseModel):
    question: str
    context: str

# Endpoints

@app.post("/register")
async def register(req: RegisterRequest):
    return auth_service.register_user(req)

@app.post("/login")
async def login(req: LoginRequest):
    return auth_service.login_user(req)

@app.post("/generate_trip")
async def generate_trip(req: TripRequest):
    print(f"🚀 Generating Trip for: {req.destination} (User: {req.username})")
    try:
        trip_plan_result = trip_service.generate_trip_plan(req)
        trip_id = db.create_new_trip(req.username, req.model_dump())
        trip_plan_result["trip_id"] = trip_id
        return trip_plan_result
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update_trip_state")
async def update_trip_state(req: TripUpdateRequest):
    success = db.update_trip_history(req.trip_id, req.chat_history)
    return {"status": "success" if success else "error"}

@app.post("/get_history_summary")
async def get_history_summary(req: HistoryRequest):
    print(f"📜 Fetching history for: {req.username}")
    trips = db.get_user_trips_summary(req.username)
    return {"trips": trips}

@app.post("/get_full_trip")
async def get_full_trip(req: GetTripRequest):
    trip = db.get_full_trip(req.trip_id)
    if trip:
        return {"status": "success", "trip": trip}
    raise HTTPException(status_code=404, detail="Trip not found")

@app.post("/delete_trip")
async def delete_trip(req: DeleteTripRequest):
    """מחיקת טיול"""
    success = db.delete_trip(req.trip_id)
    return {"status": "success" if success else "error"}

@app.post("/generate_image")
async def generate_image(req: ImageRequest):
    return image_service.generate_trip_image(req.destination, req.interest)

@app.post("/refine_trip")
async def refine_trip(req: RefineRequest):
    return trip_service.refine_trip_plan(req.current_plan, req.instruction)

@app.post("/ask_question")
async def ask_question(req: ChatRequest):
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key: return {"answer": "Error: Missing API Key"}
        
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