from fastapi import APIRouter
from pydantic import BaseModel
from server.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])

# Schema for incoming data
class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/register")
async def register(data: LoginRequest):
    # Calls service and returns exactly what service returns 
    # (e.g., {"status": "success", "message": "..."})
    return await auth_service.register_user(data)

@router.post("/login")
async def login(data: LoginRequest):
    # Calls service and returns exactly what service returns
    # (e.g., {"status": "success", "username": "..."})
    return await auth_service.login_user(data)