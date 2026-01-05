import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from server.core.config import settings

# Define Requests locally or import them if you have a shared models folder
class GenerateTripRequest(BaseModel):
    destination: str
    origin: str
    budget: str
    currency: str
    interests: str
    start_date: str
    end_date: str
    username: Optional[str] = "guest"  # Added username field

class RefineTripRequest(BaseModel):
    trip_id: str
    instructions: str

class HistoryRequest(BaseModel):
    username: str

class TripIdRequest(BaseModel):
    trip_id: str

class FlightRequest(BaseModel):
    origin: str = "Unknown"  # Use alias='from' in pydantic if needed, but client sends "from"
    to: str
    date: str

    class Config:
        fields = {'origin': 'from'} # Map 'from' JSON field to 'origin' python var

class BudgetRequest(BaseModel):
    budget: str

class UpdateStateRequest(BaseModel):
    trip_id: str
    chat_history: list

# Router with prefix matches client calls (e.g. /trips/generate)
router = APIRouter(prefix="/trips", tags=["Trips"])

# --- 1. GENERATE TRIP (Real Logic Restored) ---
@router.post("/generate")
async def generate_trip(req: GenerateTripRequest):
    """
    Orchestrates the Trip Creation:
    1. App Server -> AI Service (Generate Plan)
    2. App Server -> Data Service (Save Event)
    """
    print(f"📡 Generating trip for {req.destination}...")
    
    async with httpx.AsyncClient() as client:
        # A. Call AI Service
        try:
            # Construct payload for AI
            ai_payload = req.model_dump()
            print(f"   -> Calling AI Service at {settings.AI_SERVICE_URL}...")
            
            ai_resp = await client.post(
                f"{settings.AI_SERVICE_URL}/generate_trip",
                json=ai_payload,
                timeout=60.0
            )
            
            if ai_resp.status_code != 200:
                print(f"AI Error: {ai_resp.text}")
                # Fallback for demo if AI service is offline
                raise Exception("AI Service Offline")
                
            plan_data = ai_resp.json()
            
        except Exception as e:
            print(f"⚠️ AI Generation Failed: {e}. Returning Mock Data.")
            # FALLBACK MOCK DATA (So your app doesn't crash if AI is off)
            plan_data = {
                "destination": req.destination,
                "summary": f"A 7-day trip to {req.destination} (AI Fallback).",
                "itinerary": [
                    {"day": 1, "activity": "Arrival"},
                    {"day": 2, "activity": "City Tour"},
                    {"day": 3, "activity": "Departure"}
                ]
            }

        # B. Save to Data Service
        try:
            print(f"   -> Saving to Data Service at {settings.DATA_SERVICE_URL}...")
            await client.post(
                f"{settings.DATA_SERVICE_URL}/events/create_trip",
                json={
                    "username": req.username, 
                    "destination": req.destination,
                    "initial_request": req.dict(),
                    "generated_plan": plan_data
                }
            )
        except Exception as e:
            print(f"⚠️ Warning: Failed to save trip to Data Service: {e}")

        # Return formatted for Client
        return {"status": "success", "trip": plan_data}

# --- 2. REFINE TRIP (Restored) ---
@router.post("/refine")
async def refine_trip(req: RefineTripRequest):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.AI_SERVICE_URL}/refine_trip",
                json=req.model_dump(),
                timeout=45.0
            )
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Refinement Failed: {str(e)}")

# --- 3. HISTORY ENDPOINTS (New Requirement) ---
@router.post("/history")
async def get_history(req: HistoryRequest):
    """Fetches user history from Data Service"""
    async with httpx.AsyncClient() as client:
        try:
            # Try to call Data Service
            resp = await client.get(f"{settings.DATA_SERVICE_URL}/users/{req.username}/trips")
            if resp.status_code == 200:
                return {"trips": resp.json()}
        except Exception:
            pass
            
    # Fallback if Data Service is empty/down
    return {
        "trips": [
            {"id": "1", "destination": "Tokyo (Mock)", "date": "2025-04-10", "budget": "$4000", "status": "Planned"},
            {"id": "2", "destination": "Paris (Mock)", "date": "2024-12-25", "budget": "€2500", "status": "Completed"}
        ]
    }

@router.post("/details")
async def get_trip_details(req: TripIdRequest):
    # Mock for now (You can connect this to Data Service later)
    return {
        "trip": {
            "id": req.trip_id,
            "destination": "Mock Destination",
            "summary": "Full details loaded from server.",
            "itinerary": []
        }
    }

@router.post("/delete")
async def delete_trip(req: TripIdRequest):
    # Mock Success
    return {"status": "success"}

@router.post("/flights")
async def get_flights(req: FlightRequest):
    # Mock Flight Data
    return {
        "flights": [
            {"carrier": "MockAir", "dep": "10:00", "arr": "14:00", "price": "$120", "stops": "Direct"},
            {"carrier": "PyPlane", "dep": "16:30", "arr": "20:45", "price": "$95", "stops": "1 Stop"}
        ]
    }

@router.post("/analyze_budget")
async def analyze_budget(req: BudgetRequest):
    # Mock Budget Breakdown
    return {
        "breakdown": {
            "Flights": "30%",
            "Accommodation": "40%",
            "Food": "20%",
            "Activities": "10%"
        }
    }

@router.post("/update_state")
async def update_trip_state(req: UpdateStateRequest):
    # This would normally save to MongoDB
    print(f"💾 Saving state for Trip {req.trip_id}: {len(req.chat_history)} items")
    return {"status": "saved"}