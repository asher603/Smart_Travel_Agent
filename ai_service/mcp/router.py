from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ai_service.schemas.api_models import TripRequest, TripResponse, ChatRequest, RefineRequest
from ai_service.core.security import security_guard
from ai_service.ml_models.analyzer import analyze_user_vibe
from ai_service.ml_models.image_generator import generate_trip_image
from ai_service.agents.travel_agent import TravelAgent

# Initialize Agent
agent = TravelAgent()
router = APIRouter()

class ImageRequest(BaseModel):
    destination: str
    interest: str

@router.post("/generate_trip")
async def generate_trip(request: TripRequest):
    print(f"📨 AI Service: Processing request for {request.destination}")

    # 1. Security Guardrail
    security_check = await security_guard.check_input(request.interest)
    if not security_check.get("safe", True):
        print(f"🚫 Security Block: {security_check['reason']}")
        raise HTTPException(status_code=400, detail=f"Security Alert: {security_check['reason']}")

    # 2. Vibe Analysis
    vibe = analyze_user_vibe(request.interest)
    print(f"🧠 Analyzed Vibe: {vibe}")

    # 3. Plan Trip
    try:
        plan = await agent.plan_trip(request, vibe)
    except Exception as e:
        print(f"❌ Planning Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate trip plan")

    # 4. Image Generation
    image_b64 = generate_trip_image(request.destination, vibe)
    plan["image_base64"] = image_b64

    return plan

@router.post("/chat")
async def chat(request: ChatRequest):
    print(f"💬 Chat Request: {request.question}")
    try:
        return await agent.chat(request)
    except Exception as e:
        print(f"❌ Chat Error: {e}")
        return {"answer": "Sorry, I'm having trouble thinking right now."}

@router.post("/generate_image")
async def generate_image_api(request: ImageRequest):
    print(f"🎨 API Request: Image for {request.destination}")
    # We map 'interest' to 'vibe' for the generator
    image_b64 = generate_trip_image(request.destination, request.interest)
    return {"image_base64": image_b64}

@router.post("/refine_trip")
async def refine_trip(request: RefineRequest):
    print(f"♻️ Refine Request: {request.instructions}")
    try:
        return await agent.refine_trip(request)
    except Exception as e:
        print(f"❌ Refine Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to refine trip")