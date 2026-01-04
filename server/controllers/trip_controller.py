import httpx
from fastapi import APIRouter, HTTPException
from server.core.config import settings
from server.models.requests import GenerateTripRequest, RefineTripRequest

router = APIRouter(tags=["Trips"])

@router.post("/generate_trip")
async def generate_trip(req: GenerateTripRequest):
    """
    Orchestrates the Trip Creation:
    1. User -> App Server (Here)
    2. App Server -> AI Service (Generate Plan)
    3. App Server -> Data Service (Save Event)
    """
    async with httpx.AsyncClient() as client:
        # 1. Delegate heavy lifting to AI Service
        print(f"📡 Calling AI Service for {req.destination}...")
        try:
            ai_resp = await client.post(
                f"{settings.AI_SERVICE_URL}/generate_trip",
                json=req.dict(),
                timeout=60.0 # AI can take time
            )
            ai_resp.raise_for_status()
            plan_data = ai_resp.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI Generation Failed: {str(e)}")

        # 2. Save result to Data Service (Event Sourcing)
        # We send a 'PlanGenerated' event to the log
        try:
            await client.post(
                f"{settings.DATA_SERVICE_URL}/events/create_trip",
                json={
                    "username": req.username, 
                    "destination": req.destination,
                    "initial_request": req.dict()
                }
            )
            # Note: In a real app, you'd get the trip_id back and use it
        except Exception as e:
            print(f"⚠️ Warning: Failed to save trip to Data Service: {e}")

        return {"status": "success", "trip_plan": plan_data}

@router.post("/refine_trip")
async def refine_trip(req: RefineTripRequest):
    """
    Forwards refinement requests (e.g., "Make it cheaper") to the AI.
    """
    async with httpx.AsyncClient() as client:
        # The AI Service should have a /refine_trip endpoint logic 
        # (Or you reuse generate with feedback context)
        response = await client.post(
            f"{settings.AI_SERVICE_URL}/refine_trip",
            json=req.model_dump(),
            timeout=45.0
        )
        return response.json()