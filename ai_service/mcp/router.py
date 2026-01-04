from fastapi import APIRouter, HTTPException
from ai_service.schemas.api_models import TripRequest, TripResponse
from ai_service.core.security import security_guard
from ai_service.ml_models.analyzer import analyze_user_vibe
from ai_service.ml_models.image_generator import generate_trip_image
from ai_service.agents.travel_agent import TravelAgent

# Initialize Agent
agent = TravelAgent()
router = APIRouter()

@router.post("/generate_trip") # Response Model can be added if schemas match perfectly
async def generate_trip(request: TripRequest):
    print(f"📨 AI Service: Processing request for {request.destination}")

    # 1. Security Guardrail
    security_check = await security_guard.check_input(request.interest)
    if not security_check.get("safe", True):
        print(f"🚫 Security Block: {security_check['reason']}")
        raise HTTPException(status_code=400, detail=f"Security Alert: {security_check['reason']}")

    # 2. Vibe Analysis (Hugging Face)
    vibe = analyze_user_vibe(request.interest)
    print(f"🧠 Analyzed Vibe: {vibe}")

    # 3. Plan Trip (LangChain Agent)
    try:
        plan = await agent.plan_trip(request, vibe)
    except Exception as e:
        print(f"❌ Planning Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate trip plan")

    # 4. Image Generation (Hugging Face FLUX)
    # Note: We return the image separately or embedded. 
    # Here we embed it into the response dictionary for simplicity.
    image_b64 = generate_trip_image(request.destination, vibe)
    plan["image_base64"] = image_b64

    return plan