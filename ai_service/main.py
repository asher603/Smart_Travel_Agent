from fastapi import FastAPI
from ai_service.api.endpoints import router as api_router
from ai_service.core.events import lifespan

app = FastAPI(title="AI Service", lifespan=lifespan)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "active", "service": "ai_service"}

# Route honeypot: Listen on all possible path prefixes

# 1. Basic path (e.g., http://ai_service:8002/generate)
app.include_router(api_router)

# 2. API prefix path (e.g., http://ai_service:8002/api/generate)
app.include_router(api_router, prefix="/api")

# 3. Trips prefix path (e.g., http://ai_service:8002/trips/generate)
app.include_router(api_router, prefix="/trips")