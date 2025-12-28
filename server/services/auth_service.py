from fastapi import HTTPException
import server.database as db

def register_user(data):
    # שימוש בפונקציה הקיימת ב-database.py
    if db.create_user(data.username, data.password):
        return {"status": "success", "message": "User created successfully"}
    raise HTTPException(status_code=400, detail="Username already exists")

def login_user(data):
    if db.verify_user(data.username, data.password):
        return {"status": "success", "username": data.username}
    raise HTTPException(status_code=401, detail="Invalid username or password")