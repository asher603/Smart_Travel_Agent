from fastapi import FastAPI
from ai_service.api.endpoints import router as api_router

app = FastAPI(title="AI Service")

# בדיקת בריאות (חשוב)
@app.get("/health")
async def health_check():
    return {"status": "active", "service": "ai_service"}

# --- מלכודת דבש: מאזינים בכל הנתיבים האפשריים ---

# 1. ניסיון בסיסי (למשל: http://ai_service:8002/generate)
app.include_router(api_router)

# 2. ניסיון עם קידומת api (למשל: http://ai_service:8002/api/generate)
app.include_router(api_router, prefix="/api")

# 3. ניסיון עם קידומת trips (למשל: http://ai_service:8002/trips/generate)
app.include_router(api_router, prefix="/trips")