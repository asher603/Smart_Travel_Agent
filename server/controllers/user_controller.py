import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from server.core.config import settings

router = APIRouter(prefix="/users", tags=["Users"])

class ProfileRequest(BaseModel):
    username: str

class ProfileUpdate(BaseModel):
    username: str
    email: Optional[str] = None
    preferences: Optional[Dict] = None

@router.post("/profile")
async def get_user_profile(req: ProfileRequest):
    async with httpx.AsyncClient() as client:
        try:
            # הפניה ל-Data Service בפורט 8003/4
            resp = await client.post(
                f"{settings.DATA_SERVICE_URL}/users/get_profile",
                json=req.dict(),
                timeout=5.0
            )
            if resp.status_code == 200:
                return resp.json()
            return {} 
        except Exception as e:
            print(f"Error fetching profile: {e}")
            raise HTTPException(status_code=500, detail="Service unavailable")

@router.post("/update")
async def update_user_profile(req: ProfileUpdate):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{settings.DATA_SERVICE_URL}/users/update_profile",
                json=req.dict(),
                timeout=5.0
            )
            return resp.json()
        except Exception as e:
            print(f"Error updating profile: {e}")
            raise HTTPException(status_code=500, detail="Update failed")

# הוסף את המודל הזה
class PasswordUpdate(BaseModel):
    username: str
    old_password: str
    new_password: str

# הוסף את ה-Endpoint הזה
@router.post("/change_password")
async def change_password(req: PasswordUpdate):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{settings.DATA_SERVICE_URL}/users/change_password",
                json=req.dict(),
                timeout=5.0
            )
            
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 401:
                raise HTTPException(status_code=401, detail="Incorrect old password")
            else:
                raise HTTPException(status_code=resp.status_code, detail="Update failed")
                
        except HTTPException as he:
            raise he
        except Exception as e:
            print(f"Error changing password: {e}")
            raise HTTPException(status_code=500, detail="Service error")