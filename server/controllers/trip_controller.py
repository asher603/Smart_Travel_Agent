import httpx
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from server.core.config import settings

# --- Request Models ---
class GenerateTripRequest(BaseModel):
    destination: str
    origin: str
    budget: str
    currency: str
    interests: str
    start_date: str
    end_date: str
    username: Optional[str] = "guest"

class RefineTripRequest(BaseModel):
    trip_id: str
    instructions: str
    current_plan: dict 

class HistoryRequest(BaseModel):
    username: str

class TripIdRequest(BaseModel):
    trip_id: str

class FlightRequest(BaseModel):
    origin: str = "Unknown" 
    to: str
    date: str
    class Config:
        fields = {'origin': 'from'}

class BudgetRequest(BaseModel):
    budget: str

class UpdateStateRequest(BaseModel):
    trip_id: str
    chat_history: list

router = APIRouter(prefix="/trips", tags=["Trips"])

# --- 1. GENERATE TRIP (STRICT MODE) ---
@router.post("/generate")
async def generate_trip(req: GenerateTripRequest):
    print(f"📡 Generating trip for {req.destination}...")
    
    # 1. Calculate Duration (Critical for AI Service)
    try:
        start = datetime.strptime(req.start_date, "%Y-%m-%d")
        end = datetime.strptime(req.end_date, "%Y-%m-%d")
        duration = (end - start).days
        if duration < 1: duration = 1
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Date Format")

    # 2. Prepare Payload for AI
    ai_payload = {
        "destination": req.destination,
        "origin": req.origin,
        "budget": req.budget,
        "currency": req.currency,
        "interest": req.interests, # Mapping 'interests' -> 'interest'
        "duration": duration,
        "start_date": req.start_date,
        "end_date": req.end_date
    }

    async with httpx.AsyncClient() as client:
        # A. Call AI Service
        try:
            print(f"   -> Calling AI Service at {settings.AI_SERVICE_URL}...")
            # We use a long timeout because AI generation is slow
            ai_resp = await client.post(
                f"{settings.AI_SERVICE_URL}/generate_trip",
                json=ai_payload,
                timeout=120.0 
            )
            
            # STRICT CHECK: If AI fails, WE FAIL. No mocks.
            if ai_resp.status_code != 200:
                print(f"❌ AI Service Error: {ai_resp.text}")
                raise HTTPException(status_code=502, detail=f"AI Service Error: {ai_resp.text}")
                
            plan_data = ai_resp.json()
            
        except httpx.ConnectError:
            print("❌ AI Service Connection Refused")
            raise HTTPException(status_code=503, detail="AI Service is unreachable (Check Docker)")
        except httpx.ReadTimeout:
            print("❌ AI Service Timed Out")
            raise HTTPException(status_code=504, detail="AI Generation Timed Out")

        # B. Save to Data Service
        new_trip_id = str(uuid.uuid4())
        plan_data["trip_id"] = new_trip_id
        
        try:
            print(f"   -> Saving Trip {new_trip_id} to Data Service...")
            save_resp = await client.post(
                f"{settings.DATA_SERVICE_URL}/events/create_trip",
                json={
                    "trip_id": new_trip_id,
                    "username": req.username, 
                    "destination": req.destination,
                    "initial_request": req.dict(),
                    "generated_plan": plan_data
                }
            )
            if save_resp.status_code not in [200, 201]:
                print(f"⚠️ Data Save Warning: {save_resp.text}")
        except Exception as e:
            print(f"⚠️ Data Service Warning: {e}")

        return {"status": "success", "trip": plan_data}

# --- 2. REFINE TRIP ---
@router.post("/refine")
async def refine_trip(req: RefineTripRequest):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.AI_SERVICE_URL}/refine_trip",
                json=req.dict(),
                timeout=60.0
            )
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Refinement Failed: {str(e)}")

# --- 3. HISTORY & DETAILS ---
@router.post("/history")
async def get_history(req: HistoryRequest):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{settings.DATA_SERVICE_URL}/users/{req.username}/trips")
            if resp.status_code == 200:
                return {"trips": resp.json()}
            return {"trips": []}
        except Exception:
            return {"trips": []}

@router.post("/details")
async def get_trip_details(req: TripIdRequest):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{settings.DATA_SERVICE_URL}/trips/{req.trip_id}")
            if resp.status_code == 200:
                return {"trip": resp.json()}
            raise HTTPException(status_code=404, detail="Trip not found")
        except Exception as e:
             raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete")
async def delete_trip(req: TripIdRequest):
    async with httpx.AsyncClient() as client:
        await client.delete(f"{settings.DATA_SERVICE_URL}/trips/{req.trip_id}")
        return {"status": "success"}

@router.post("/update_state")
async def update_trip_state(req: UpdateStateRequest):
    async with httpx.AsyncClient() as client:
        await client.put(f"{settings.DATA_SERVICE_URL}/trips/{req.trip_id}/state", json={"chat_history": req.chat_history})
        return {"status": "saved"}

# --- 4. UTILITIES ---
@router.post("/flights")
async def get_flights(req: FlightRequest):
    return {
        "flights": [
             {"carrier": "System Estimate", "dep": "TBD", "arr": "TBD", "price": "Check Operator", "stops": "N/A"}
        ]
    }

@router.post("/analyze_budget")
async def analyze_budget(req: BudgetRequest):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{settings.AI_SERVICE_URL}/analyze_budget", json={"budget": req.budget})
            if resp.status_code == 200: return resp.json()
        except: pass
    return {"breakdown": {"Allocated": "100%", "Notes": "AI Service Unavailable"}}