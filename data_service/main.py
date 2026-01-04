import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv
from data_service.api.routes import router
from data_service.core.db import init_mongo

load_dotenv()

app = FastAPI(title="Data Service (Event Store)")

@app.on_event("startup")
def startup_db():
    init_mongo()

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)