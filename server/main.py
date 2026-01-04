import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.core.config import settings
from server.controllers import auth_controller, trip_controller, services_controller

app = FastAPI(title="Smart Travel App Server", version="1.0")

# CORS is crucial because your Client (Desktop App) might technically 
# be "external" if you run it on a different machine.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Controllers
app.include_router(auth_controller.router)
app.include_router(trip_controller.router)
app.include_router(services_controller.router)

@app.get("/")
def root():
    return {"message": "Travel App Server Running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)