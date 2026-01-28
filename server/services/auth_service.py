import httpx
from fastapi import HTTPException
from server.core.config import settings

# Helper for async HTTP requests
async def _call_data_service(endpoint: str, data: dict):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.DATA_SERVICE_URL}{endpoint}", 
                json=data,
                timeout=10.0
            )
            return response
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Data Service Unavailable")

async def register_user(data):
    """
    Sends registration data to Data Service.
    """
    response = await _call_data_service("/users/register", {
        "username": data.username,
        "password": data.password
    })

    if response.status_code == 400:
        raise HTTPException(status_code=400, detail="Username already taken. Please choose another.")
    
    if response.status_code != 200:
         raise HTTPException(status_code=500, detail="Registration failed. Please try again.")

    return {"status": "success", "message": "User created successfully"}

async def login_user(data):
    """
    Sends login credentials to Data Service for verification.
    """
    response = await _call_data_service("/users/verify", {
        "username": data.username,
        "password": data.password
    })

    if response.status_code == 401:
        # Get specific error message from data service
        try:
            error_detail = response.json().get("detail", "Invalid credentials")
        except:
            error_detail = "Invalid credentials"
        raise HTTPException(status_code=401, detail=error_detail)
    
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Login check failed")

    return {"status": "success", "username": data.username}