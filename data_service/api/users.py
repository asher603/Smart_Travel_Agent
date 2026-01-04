from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import bcrypt
from datetime import datetime
from data_service.core.db import get_db

router = APIRouter(prefix="/users", tags=["Users"])

class UserAuth(BaseModel):
    username: str
    password: str

@router.post("/register")
def register(user: UserAuth):
    db = get_db()
    users_col = db["users"]
    
    # Check if user already exists
    if users_col.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="User exists")
    
    # Hash password securely
    hashed = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    
    users_col.insert_one({
        "username": user.username,
        "password": hashed,
        "created_at": datetime.utcnow()
    })
    return {"status": "created"}

@router.post("/verify")
def verify(user: UserAuth):
    db = get_db()
    users_col = db["users"]
    
    # Find user
    doc = users_col.find_one({"username": user.username})
    if not doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check password hash
    # Note: doc["password"] comes out as bytes from Mongo, so we might need to handle encoding
    stored_pass = doc["password"]
    if isinstance(stored_pass, str):
        stored_pass = stored_pass.encode('utf-8')

    if bcrypt.checkpw(user.password.encode('utf-8'), stored_pass):
        return {"status": "valid"}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")