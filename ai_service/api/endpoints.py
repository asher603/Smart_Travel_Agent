from fastapi import APIRouter, HTTPException
import logging
from ai_service.schemas.api_models import TripRequest, ChatRequest, RefineRequest
from ai_service.agents.travel_agent import TravelAgent

# שים לב: לא מגדירים כאן prefix, זה קורה ב-main.py
router = APIRouter()
logger = logging.getLogger("uvicorn")

@router.post("/generate")
async def generate_trip(request: TripRequest):
    logger.info(f"📝 Handling request for: {request.destination}")
    try:
        agent = TravelAgent()
        # מנסים לקבל טיול (כרגע גם אם ה-MCP נכשל, הוא יחזיר משהו מה-LLM)
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