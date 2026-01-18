from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import bcrypt
from datetime import datetime
from data_service.core.db import get_db
from typing import Optional, Dict

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
    stored_pass = doc["password"]
    if isinstance(stored_pass, str):
        stored_pass = stored_pass.encode('utf-8')

    if bcrypt.checkpw(user.password.encode('utf-8'), stored_pass):
        return {"status": "valid"}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

class UserProfileRequest(BaseModel):
    username: str

@router.post("/get_profile")
def get_profile(req: UserProfileRequest):
    db = get_db()
    # שליפת המשתמש ללא הסיסמה וה-ID הפנימי
    user = db["users"].find_one({"username": req.username}, {"_id": 0, "password": 0})
    
    if not user:
        # אם המשתמש לא נמצא (נדיר), נחזיר מבנה ריק תקין
        return {"username": req.username, "preferences": {}}
    
    return user

class UserProfileUpdate(BaseModel):
    username: str
    email: Optional[str] = None
    preferences: Optional[Dict] = None

@router.post("/update_profile")
def update_profile(data: UserProfileUpdate):
    db = get_db()
    
    # בניית אובייקט העדכון דינמית (רק שדות שנשלחו)
    update_fields = {}
    if data.email is not None:
        update_fields["email"] = data.email
    if data.preferences is not None:
        update_fields["preferences"] = data.preferences

    if not update_fields:
        return {"status": "no_change"}

    result = db["users"].update_one(
        {"username": data.username},
        {"$set": update_fields}
    )
    
    # --- תיקון: החזרת שגיאה אם המשתמש לא נמצא ---
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"User {data.username} not found")
    
    return {"status": "updated"}

# מחלקה לקבלת הנתונים
class UserPasswordUpdate(BaseModel):
    username: str
    old_password: str
    new_password: str

@router.post("/change_password")
def change_user_password(data: UserPasswordUpdate):
    db = get_db()
    users_col = db["users"]
    
    # 1. שליפת המשתמש
    user = users_col.find_one({"username": data.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 2. אימות הסיסמה הישנה
    stored_pass = user["password"]
    if isinstance(stored_pass, str):
        stored_pass = stored_pass.encode('utf-8')
    
    if not bcrypt.checkpw(data.old_password.encode('utf-8'), stored_pass):
        raise HTTPException(status_code=401, detail="Incorrect old password")
    
    # 3. הצפנת הסיסמה החדשה ושמירה
    new_hashed = bcrypt.hashpw(data.new_password.encode('utf-8'), bcrypt.gensalt())
    
    users_col.update_one(
        {"username": data.username},
        {"$set": {"password": new_hashed}}
    )
    
    return {"status": "password_updated"}