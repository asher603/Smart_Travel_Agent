from fastapi import APIRouter, HTTPException
import logging
from ai_service.schemas.api_models import TripRequest
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