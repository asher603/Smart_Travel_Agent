from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Smart Travel Agent API")

# הגדרת CORS כדי לאפשר ללקוח (Desktop App) לגשת לשרת
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "Server is running", "service": "Smart Travel Agent"}

@app.get("/generate_trip/{destination}")
def generate_trip(destination: str):
    # כאן בעתיד יתבצע החיבור ל-AI Agent ול-DB
    # כרגע נחזיר תשובה דמה (Dummy) כדי לבדוק שהכל עובד
    return {
        "destination": destination,
        "itinerary": f"Day 1 in {destination}: Visit the main square.",
        "budget": 1500,
        "weather": "Sunny"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)