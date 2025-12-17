import sys
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- הגדרת נתיבים כדי למצוא את התיקיות השכנות ---
# זה קריטי כדי שהשרת יוכל לייבא את ai_agent ואת database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_agent.agent_core import TravelAgent
import server.database as db  # הייבוא של ה-DB החדש

# --- יצירת האפליקציה (השורה שהייתה חסרה לך) ---
app = FastAPI(title="Smart Travel Agent API")

# --- הגדרות CORS (כדי שהריאקט יוכל לדבר עם השרת) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # בפרודקשן מומלץ להגביל, לפיתוח זה מעולה
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- אתחול המשתנים ---
agent = TravelAgent()  # טוען את המודל של אולמה

# הפעלה של החיבור ל-DB בעליית השרת
@app.on_event("startup")
def startup_db_client():
    db.init_db()

# --- המודל של הבקשה ---
class TripRequest(BaseModel):
    query: str

# --- הנתיבים (Endpoints) ---

@app.get("/")
def read_root():
    return {"status": "Server is running", "db_status": "Check logs for MongoDB connection"}

@app.get("/generate_trip/{destination}")
def generate_trip(destination: str):
    print(f"🚀 Received request for: {destination}")

    try:
        # 1. תיעוד: המשתמש ביקש טיול
        db.log_event("TripRequested", {"destination": destination})

        # 2. הפעלת ה-AI (לוקח כמה שניות)
        result = agent.generate_response(destination)
        
        # 3. תיעוד: הטיול נוצר בהצלחה
        db.log_event("TripGenerated", result)
        
        return result

    except Exception as e:
        # 4. תיעוד: קרתה שגיאה
        error_msg = {"error": str(e), "destination": destination}
        db.log_event("ErrorOccurred", error_msg)
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
def get_history():
    """
    נתיב בונוס: מאפשר לראות את כל ההיסטוריה השמורה במונגו
    """
    events = db.get_all_events()
    return {"count": len(events), "events": events}

# --- אפשרות להריץ גם ישירות דרך פייתון (אופציונלי) ---
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)