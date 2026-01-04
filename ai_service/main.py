import uvicorn
from fastapi import FastAPI
from ai_service.core.events import lifespan
from ai_service.core.config import settings
from ai_service.mcp.router import router as mcp_router

# 1. Initialize App with Lifespan (Startup/Shutdown logic)
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan 
)

# 2. Register Routes
app.include_router(mcp_router)

@app.get("/health")
def health_check():
    return {
        "status": "active", 
        "mode": "debug" if settings.DEBUG_MODE else "production"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8001, 
        reload=settings.DEBUG_MODE
    )