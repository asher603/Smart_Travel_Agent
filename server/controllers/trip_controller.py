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

# ============================================================================
# Request Models
# ============================================================================

class GenerateTripRequest(BaseModel):
    """
    Payload for generating a new trip.
    Includes user preferences, budget, and travel dates.
    """
    destination: str
    origin: str
    budget: str
    currency: str
    interests: str
    start_date: str
    end_date: str
    username: Optional[str] = "guest"
    model: Optional[str] = "gemini"
    gender: Optional[str] = "male"

class RefineTripRequest(BaseModel):
    """
    Payload for refining an existing trip plan based on user instructions.
    """
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

class BudgetAnalysisRequest(BaseModel):
    destination: str
    origin: str
    duration: int
    budget: str
    currency: str
    interest: str
    model: str = "gemini"

class UpdateStateRequest(BaseModel):
    trip_id: str
    chat_history: list

# ============================================================================
# API Router
# ============================================================================

router = APIRouter(prefix="/trips", tags=["Trips"])

# --- 1. GENERATE TRIP ---
@router.post("/generate")
async def generate_trip(req: GenerateTripRequest):
    """
    Main endpoint to generate a travel itinerary.
    
    Process:
    1. Calculates trip duration.
    2. Fetches user email from Data Service (for automation).
    3. Calls AI Service to generate the plan.
    4. Saves the generated trip to Data Service (MongoDB).
    """
    print(f"📡 Generating trip for {req.destination}...")
    
    # 1. Calculate Duration
    try:
        start = datetime.strptime(req.start_date, "%Y-%m-%d")
        end = datetime.strptime(req.end_date, "%Y-%m-%d")
        duration = (end - start).days
        if duration < 1: duration = 1
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Date Format")

    async with httpx.AsyncClient() as client:
        
        # ---------------------------------------------------------
        # 2. Fetch User Email (Fix for n8n Automation)
        # ---------------------------------------------------------
        # We attempt to fetch the user's email from the profile service
        # so the AI service can pass it to the automation workflow.
        user_email = None # Default fallback
        
        if req.username and req.username.lower() != "guest":
            try:
                # Reuse the client to call Data Service
                profile_resp = await client.post(
                    f"{settings.DATA_SERVICE_URL}/users/get_profile",
                    json={"username": req.username},
                    timeout=2.0
                )
                
                if profile_resp.status_code == 200:
                    profile_data = profile_resp.json()
                    if profile_data.get("email"):
                        user_email = profile_data["email"]
                        print(f"✅ Email fetched for automation: {user_email}")
                    else:
                        print("⚠️ User has no email saved in profile.")
            except Exception as e:
                print(f"⚠️ Could not fetch email for automation: {e}")

        # ---------------------------------------------------------
        # 3. Prepare Payload for AI Service
        # ---------------------------------------------------------
        ai_payload = {
            "destination": req.destination,
            "origin": req.origin,
            "budget": req.budget,
            "currency": req.currency,
            "interest": req.interests,
            "duration": duration,
            "start_date": req.start_date,
            "end_date": req.end_date,
            "model": req.model,
            "email": user_email,  # <--- Injected email here
            "gender": req.gender or "male"
        }

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
            
            # Inject Metadata into the Plan object
            plan_data["origin"] = req.origin
            plan_data["destination"] = req.destination
            plan_data["start_date"] = req.start_date
            plan_data["budget"] = req.budget
            plan_data["currency"] = req.currency
            
        except httpx.ConnectError:
            print("❌ AI Service Connection Refused")
            raise HTTPException(status_code=503, detail="AI Service is unreachable")
        except httpx.ReadTimeout:
            print("❌ AI Service Timed Out")
            raise HTTPException(status_code=504, detail="AI Generation Timed Out")
        except Exception as e:
            print(f"⚠️ AI Generation Failed: {e}. Returning Mock Data.")
            raise HTTPException(status_code=500, detail=f"AI Generation Failed: {str(e)}")

        # ---------------------------------------------------------
        # 4. Save to Data Service (Persistence)
        # ---------------------------------------------------------
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
                timeout=10.0 # Short timeout to prevent hanging
            )
            
            if save_resp.status_code not in [200, 201]:
                print(f"❌ CRITICAL: Data Service failed to save trip! Status: {save_resp.status_code}, Body: {save_resp.text}")
            else:
                print("✅ Trip saved to history successfully.")
                
        except Exception as e:
            print(f"❌ CRITICAL: Exception saving to Data Service: {e}")
            # Note: We still return the plan to the user even if saving failed.

        return {"status": "success", "trip": plan_data}

# --- 2. REFINE TRIP ---
@router.post("/refine")
async def refine_trip(req: RefineTripRequest):
    """
    Sends modification instructions to the AI Service to update an existing plan.
    """
    print(f"♻️ Refining Trip {req.trip_id} with instruction: {req.instructions}")
    
    async with httpx.AsyncClient() as client:
        try:
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
    """
    Fetches the list of past trips for a specific user.
    """
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
    """
    Retrieves the full details of a specific trip by ID.
    """
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
    """
    Deletes a trip from the database.
    """
    async with httpx.AsyncClient() as client:
        await client.delete(f"{settings.DATA_SERVICE_URL}/trips/{req.trip_id}")
        return {"status": "success"}

@router.post("/update_state")
async def update_trip_state(req: UpdateStateRequest):
    """
    Updates the state of a trip (e.g., chat history) without regenerating the plan.
    """
    async with httpx.AsyncClient() as client:
        await client.put(f"{settings.DATA_SERVICE_URL}/trips/{req.trip_id}/state", json={"chat_history": req.chat_history})
        return {"status": "saved"}

# --- 4. UTILITIES ---
@router.post("/flights")
def get_flights(req: FlightRequest):
    """
    Proxy endpoint to search for flights using the Flight Service.
    """
    print(f"✈️ Searching flights: {req.origin} -> {req.to} on {req.date}")
    results = flight_service.search_flights(req.origin, req.to, req.date)
    if isinstance(results, dict) and "error" in results:
        return {"flights": []}
    return {"flights": results}

@router.post("/analyze_budget")
async def analyze_budget(req: BudgetAnalysisRequest):
    print(f"💰 AI Analyzing budget for {req.destination}...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Forward to AI Service
            ai_resp = await client.post(
                f"{settings.AI_SERVICE_URL}/analyze_budget",
                json=req.dict(),
                timeout=60.0 
            )
            
            if ai_resp.status_code == 200:
                return ai_resp.json() # Returns { "breakdown": { ... } }
            
            print(f"⚠️ AI Budget Error: {ai_resp.text}")
            raise HTTPException(status_code=502, detail="AI Budget Analysis failed")

        except Exception as e:
            print(f"❌ Budget Error: {e}")
            # Fallback if AI service is totally down
            return {"breakdown": {"Flights": 0, "Accommodation": 0, "Food": 0, "Activities": 0}}