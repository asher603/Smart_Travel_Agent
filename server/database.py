import pymongo
import certifi
import os
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

# --- שלב 1: טעינת משתני הסביבה ---
# הפקודה find_dotenv מחפשת את קובץ ה-.env גם בתיקיות למעלה (בתיקייה הראשית)
load_dotenv(find_dotenv())

# --- שלב 2: שליפת הכתובת ---
# ודא שבקובץ .env שלך המשתנה נקרא בדיוק MONGODB_URI
CONNECTION_STRING = os.getenv("MONGODB_URI")

# הגדרות קבועות
DB_NAME = "smart_travel_agent_db"
COLLECTION_NAME = "events"

# משתנים שיחזיקו את החיבור
client = None
db = None

def init_db():
    """
    יצירת החיבור לשרת של מונגו בענן.
    פונקציה זו נקראת פעם אחת כשהשרת עולה.
    """
    global client, db
    
    if not CONNECTION_STRING:
        print("❌ Error: MONGODB_URI not found in .env file")
        return

    try:
        # השימוש ב-certifi פותר בעיות SSL נפוצות בווינדוס
        client = pymongo.MongoClient(CONNECTION_STRING, tlsCAFile=certifi.where())
        db = client[DB_NAME]
        
        # בדיקת 'פינג' כדי לוודא שהחיבור הצליח
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas (Cloud)!")
        
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")

def log_event(event_type: str, data: dict):
    """
    שומר נתונים במונגו (כמו בקשה לטיול או תוצאה)
    """
    if db is None:
        init_db()
    
    if db is not None:
        event = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "payload": data
        }
        try:
            db[COLLECTION_NAME].insert_one(event)
            print(f"☁️  Event saved to cloud: {event_type}")
        except Exception as e:
            print(f"⚠️ Failed to save event: {e}")

def get_all_events():
    """
    שולף את כל ההיסטוריה מהענן
    """
    if db is None:
        init_db()
        
    if db is not None:
        # שולף הכל, ממיין לפי זמן (הכי חדש למעלה), ומסתיר את ה-ID הפנימי
        return list(db[COLLECTION_NAME].find({}, {'_id': 0}).sort("timestamp", -1))
    
    return []