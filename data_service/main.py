import uvicorn
from fastapi import FastAPI
from data_service.core.config import settings
from data_service.core.db import close_mongo, init_mongo

# Import the routers
from data_service.api.routes import router as event_router
from data_service.api.users import router as user_router

app = FastAPI(title=settings.APP_NAME)

# Database Lifecycle
@app.on_event("startup")
async def startup_db_client():
    init_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    close_mongo()

app.include_router(event_router)
app.include_router(user_router)

@app.get("/health")
def health_check():
    return {"status": "active", "service": "data_service"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)