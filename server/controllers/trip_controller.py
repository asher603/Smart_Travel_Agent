import httpx
import uuid
import re
import random
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from server.core.config import settings
from server.services.flight_service import flight_service

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
    model: Optional[str] = "gemini"

class RefineTripRequest(BaseModel):
    trip_id: str
    instructions: str
    current_plan: Dict[str, Any]
    model: Optional[str] = "gemini"

class HistoryRequest(BaseModel):
    username: str

class TripIdRequest(BaseModel):
    trip_id: str

class FlightRequest(BaseModel):
    origin: str = Field(default="Unknown", alias="from")
    to: str
    date: str

class BudgetRequest(BaseModel):
    budget: str

class UpdateStateRequest(BaseModel):
    trip_id: str
    chat_history: list

router = APIRouter(prefix="/trips", tags=["Trips"])

# --- 1. GENERATE TRIP ---
@router.post("/generate")
async def generate_trip(req: GenerateTripRequest):
    print(f"📡 Generating trip for {req.destination}...")
    
    # 1. Calculate Duration
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
        "interest": req.interests,
        "duration": duration,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "model": req.model
    }

    async with httpx.AsyncClient() as client:
        # A. Call AI Service
        try:
            print(f"   -> Calling AI Service at {settings.AI_SERVICE_URL}/generate...")
            ai_resp = await client.post(
                f"{settings.AI_SERVICE_URL}/generate",
                json=ai_payload,
                timeout=300.0 
            )
            
            if ai_resp.status_code != 200:
                print(f"❌ AI Service Error: {ai_resp.text}")
                raise HTTPException(status_code=502, detail=f"AI Service Error: {ai_resp.text}")
                
            plan_data = ai_resp.json()
            
            # Inject Metadata into Plan
            plan_data["origin"] = req.origin
            plan_data["destination"] = req.destination
            plan_data["start_date"] = req.start_date
            
        except httpx.ConnectError:
            print("❌ AI Service Connection Refused")
            raise HTTPException(status_code=503, detail="AI Service is unreachable")
        except httpx.ReadTimeout:
            print("❌ AI Service Timed Out")
            raise HTTPException(status_code=504, detail="AI Generation Timed Out")
        except Exception as e:
            print(f"⚠️ AI Generation Failed: {e}. Returning Mock Data.")
            raise HTTPException(status_code=500, detail=f"AI Generation Failed: {str(e)}")

        # B. Save to Data Service (תיקון לבעיית ההיסטוריה)
        new_trip_id = str(uuid.uuid4())
        plan_data["trip_id"] = new_trip_id
        
        try:
            print(f"   -> Saving Trip {new_trip_id} to Data Service...")
            
            save_payload = {
                "trip_id": new_trip_id,
                "username": req.username, 
                "destination": req.destination,
                "origin": req.origin, 
                "initial_request": req.dict(),
                "generated_plan": plan_data
            }
            
            save_resp = await client.post(
                f"{settings.DATA_SERVICE_URL}/events/create_trip",
                json=save_payload,
                timeout=10.0 # Timeout קצר, שלא יתקע אם ה-DB איטי
            )
            
            if save_resp.status_code not in [200, 201]:
                # לוג קריטי: אם זה קורה, הטיול לא נשמר
                print(f"❌ CRITICAL: Data Service failed to save trip! Status: {save_resp.status_code}, Body: {save_resp.text}")
            else:
                print("✅ Trip saved to history successfully.")
                
        except Exception as e:
            # כאן אנחנו תופסים שגיאות חיבור ל-Data Service
            print(f"❌ CRITICAL: Exception saving to Data Service: {e}")
            # הערה: אנחנו עדיין מחזירים את הטיול למשתמש כדי לא 'להעניש' אותו,
            # אבל בקונסול תראה עכשיו בבירור למה זה לא נשמר.

        return {"status": "success", "trip": plan_data}

# --- 2. REFINE TRIP ---
@router.post("/refine")
async def refine_trip(req: RefineTripRequest):
    print(f"♻️ Refining Trip {req.trip_id} with instruction: {req.instructions}")
    
    async with httpx.AsyncClient() as client:
        try:
            # Note: You might need to add /refine endpoint to AI Service later
            ai_resp = await client.post(
                f"{settings.AI_SERVICE_URL}/refine",
                json=req.model_dump(),
                timeout=300.0
            )
            
            if ai_resp.status_code != 200:
                raise HTTPException(status_code=ai_resp.status_code, detail=f"AI Error: {ai_resp.text}")

            refined_plan = ai_resp.json()
            return {"status": "success", "trip_plan": refined_plan}

        except Exception as e:
            print(f"❌ Refine Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# --- 3. HISTORY & DETAILS ---
@router.post("/history")
async def get_history(req: HistoryRequest):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{settings.DATA_SERVICE_URL}/user/{req.username}/summary")
            if resp.status_code == 200:
                return {"trips": resp.json()}
            print(f"⚠️ History fetch failed: {resp.status_code}")
            return {"trips": []}
        except Exception as e:
            print(f"⚠️ History fetch error: {e}")
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
def get_flights(req: FlightRequest):
    print(f"✈️ Searching flights: {req.origin} -> {req.to} on {req.date}")
    results = flight_service.search_flights(req.origin, req.to, req.date)
    if isinstance(results, dict) and "error" in results:
        return {"flights": []}
    return {"flights": results}

@router.post("/analyze_budget")
async def analyze_budget(req: BudgetRequest):
    print(f"💰 Analyzing budget: {req.budget}")
    try:
        matches = re.findall(r"[-+]?\d*\.\d+|\d+", req.budget.replace(",", ""))
        total = float(matches[0]) if matches else 2000.0
    except: total = 2000.0

    f_share = 0.35 + random.uniform(-0.05, 0.05)
    h_share = 0.35 + random.uniform(-0.05, 0.05)
    fd_share = 0.20 + random.uniform(-0.03, 0.03)
    a_share = 1.0 - (f_share + h_share + fd_share)

    def fmt(amount, share): return f"${int(amount)} ({int(share*100)}%)"

    return {
        "breakdown": {
            "Flights": fmt(total * f_share, f_share),
            "Accommodation": fmt(total * h_share, h_share),
            "Food": fmt(total * fd_share, fd_share),
            "Activities": fmt(total * a_share, a_share)
        }
    }