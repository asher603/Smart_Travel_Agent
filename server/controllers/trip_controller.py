import httpx
import uuid
import re
import random
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
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

class RefineTripRequest(BaseModel):
    trip_id: str
    instructions: str
    current_plan: dict 

class HistoryRequest(BaseModel):
    username: str

class TripIdRequest(BaseModel):
    trip_id: str

class FlightRequest(BaseModel):
    # Pydantic V2 Fix: Using Field(alias=...) instead of Config.fields
    origin: str = Field(default="Unknown", alias="from")
    to: str
    date: str

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
        "end_date": req.end_date
    }

    async with httpx.AsyncClient() as client:
        # A. Call AI Service
        try:
            print(f"   -> Calling AI Service at {settings.AI_SERVICE_URL}...")
            ai_resp = await client.post(
                f"{settings.AI_SERVICE_URL}/generate_trip",
                json=ai_payload,
                timeout=120.0 
            )
            
            if ai_resp.status_code != 200:
                print(f"❌ AI Service Error: {ai_resp.text}")
                raise HTTPException(status_code=502, detail=f"AI Service Error: {ai_resp.text}")
                
            plan_data = ai_resp.json()
            
        except httpx.ConnectError:
            print("❌ AI Service Connection Refused")
            raise HTTPException(status_code=503, detail="AI Service is unreachable")
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
def get_flights(req: FlightRequest):
    """
    Connects to the REAL FlightService (Amadeus API).
    """
    print(f"✈️ Searching flights: {req.origin} -> {req.to} on {req.date}")
    
    results = flight_service.search_flights(req.origin, req.to, req.date)
    
    if isinstance(results, dict) and "error" in results:
        print(f"❌ Flight API Error: {results['error']}")
        return {"flights": []}
        
    return {"flights": results}

@router.post("/analyze_budget")
async def analyze_budget(req: BudgetRequest):
    """
    Analyzes the budget string (e.g. "$2000") and returns a calculated breakdown.
    This replaces the static fake data with dynamic calculations.
    """
    print(f"💰 Analyzing budget input: {req.budget}")
    
    # 1. Extract numeric value from string (handle "$", ",", etc.)
    try:
        # Finds the first number (integer or float) in the string
        matches = re.findall(r"[-+]?\d*\.\d+|\d+", req.budget.replace(",", ""))
        if matches:
            total_budget = float(matches[0])
        else:
            total_budget = 2000.0 # Default fallback if no number found
    except Exception:
        total_budget = 2000.0

    # 2. Define Distribution Ratios (with slight randomness to feel 'alive')
    # Base: Flights ~35%, Hotel ~35%, Food ~20%, Activities ~10%
    flight_share = 0.35 + random.uniform(-0.05, 0.05)
    hotel_share = 0.35 + random.uniform(-0.05, 0.05)
    food_share = 0.20 + random.uniform(-0.03, 0.03)
    
    # Normalize to ensure we don't exceed 100% before activities
    current_sum = flight_share + hotel_share + food_share
    if current_sum > 0.95:
        factor = 0.9 / current_sum
        flight_share *= factor
        hotel_share *= factor
        food_share *= factor
    
    # The rest goes to activities
    activity_share = 1.0 - (flight_share + hotel_share + food_share)

    # 3. Calculate Amounts
    flights_cost = int(total_budget * flight_share)
    hotel_cost = int(total_budget * hotel_share)
    food_cost = int(total_budget * food_share)
    activities_cost = int(total_budget * activity_share)

    # 4. Format Output
    def fmt(amount, share):
        return f"${amount} ({int(share*100)}%)"

    return {
        "breakdown": {
            "Flights": fmt(flights_cost, flight_share),
            "Accommodation": fmt(hotel_cost, hotel_share),
            "Food": fmt(food_cost, food_share),
            "Activities": fmt(activities_cost, activity_share)
        }
    }