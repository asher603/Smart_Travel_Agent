import httpx
from fastapi import APIRouter
from pydantic import BaseModel
from server.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI"])

class ImageRequest(BaseModel):
    destination: str
    interest: str

class ChatRequest(BaseModel):
    question: str
    context: str
    model: str = "gemini"

@router.post("/generate_image")
async def generate_image(req: ImageRequest):
    """
    Proxies request to AI Service or returns a placeholder if offline.
    """
    # 1. Try Real AI Service
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.AI_SERVICE_URL}/generate_image",
                json=req.dict(),
                timeout=10.0
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass # Fallback

    # 2. Fallback (Mock) - Returns a placeholder image from Unsplash source or similar
    # We return None so the client shows a "No Image" or handled error, 
    # OR we can return a sample base64 if you had one. 
    # For now, let's return a dummy structure so the client doesn't crash.
    return {"image_base64": None} 

@router.post("/ask")
async def ask_chat(req: ChatRequest):
    """
    Handles chat questions about the trip.
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.AI_SERVICE_URL}/chat",
                json=req.dict(),
                timeout=300.0
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass

    # Fallback Mock Response
    return {"answer": f"I see you're asking about '{req.question}'. (AI Service is offline, but I received your context regarding {req.context[:20]}...)"}