import httpx
from fastapi import APIRouter, HTTPException
from server.core.config import settings
from pydantic import BaseModel

router = APIRouter(tags=["Auth"])

class AuthRequest(BaseModel):
    username: str
    password: str

@router.post("/auth/register")
async def register_user(data: AuthRequest):
    """
    Proxies the registration request to the Data Service.
    """
    async with httpx.AsyncClient() as client:
        try:
            # We assume the Data Service exposes a user management endpoint
            response = await client.post(
                f"{settings.DATA_SERVICE_URL}/users/register",
                json=data.dict()
            )
            if response.status_code == 400:
                raise HTTPException(status_code=400, detail="Username already exists")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Data Service unavailable")

@router.post("/auth/login")
async def login_user(data: AuthRequest):
    """
    Proxies the login check to the Data Service.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.DATA_SERVICE_URL}/users/verify",
                json=data.dict()
            )
            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            return response.json() # Should return {"token": ..., "username": ...}
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Data Service unavailable")