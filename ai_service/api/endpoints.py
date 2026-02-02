from fastapi import APIRouter, HTTPException
import logging
from ai_service.schemas.api_models import TripRequest, ChatRequest, RefineRequest, ImageRequest, BudgetAnalysisRequest
from ai_service.agents.travel_agent import TravelAgent
from ai_service.ml_models.image_generator import generate_trip_image

router = APIRouter()
logger = logging.getLogger("uvicorn")

@router.post("/generate")
async def generate_trip(request: TripRequest):
    logger.info(f"📝 Handling request for: {request.destination}")
    try:
        agent = TravelAgent()
        # Attempt to get trip (returns LLM result even if MCP fails)
        result = await agent.plan_trip(request, analyzed_vibe="fun")
        return result
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/chat")
async def chat_about_trip(request: ChatRequest):
    logger.info(f"💬 Handling question: {request.question}")
    try:
        agent = TravelAgent()
        result = await agent.answer_question(request)
        return result
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/refine")
async def refine_trip_plan(request: RefineRequest):
    logger.info(f"♻️ Handling refinement request")
    try:
        agent = TravelAgent()
        result = await agent.refine_trip(request)
        return result
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/generate_image")
async def create_image(req: ImageRequest):
    logger.info(f"🎨 Generating image for: {req.destination}")
    try:
        # We pass the user's 'interest' as the 'vibe' for the prompt
        image_b64 = generate_trip_image(req.destination, req.interest)
        
        if not image_b64:
            raise HTTPException(status_code=500, detail="Image generation returned empty")
            
        return {"image_base64": image_b64}
    except Exception as e:
        logger.error(f"❌ Image Error: {e}")
        # Return None or error so the server can handle the fallback
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/analyze_budget")
async def analyze_budget(req: BudgetAnalysisRequest):
    logger.info(f"💰 Analyzing budget for: {req.destination}")
    try:
        agent = TravelAgent()
        result = await agent.analyze_budget(req)
        return result
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))