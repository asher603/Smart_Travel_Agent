import pymongo
import certifi
import os
import bcrypt  # <--- הוספנו את זה
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

CONNECTION_STRING = os.getenv("MONGODB_URI")
DB_NAME = "smart_travel_agent_db"
COLLECTION_EVENTS = "events"
COLLECTION_USERS = "users"  # <--- קולקציה חדשה למשתמשים

client = None
db = None

def init_db():
    global client, db
    if not CONNECTION_STRING:
        print("❌ Error: MONGODB_URI not found")
        return

    try:
        client = pymongo.MongoClient(CONNECTION_STRING, tlsCAFile=certifi.where())
        db = client[DB_NAME]
        # בדיקת חיבור
        client.admin.command('ping')
        print("✅ MongoDB Connected!")
    except Exception as e:
        print(f"❌ MongoDB Error: {e}")

# --- ניהול משתמשים ---
def create_user(username, password):
    if db is None: init_db()
    if db is not None:
        # 1. בדיקה אם המשתמש כבר קיים
        if db[COLLECTION_USERS].find_one({"username": username}):
            return False  # המשתמש כבר קיים
        
        # 2. הצפנת הסיסמה
        # ממירים ל-bytes, מצפינים, ושומרים
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # 3. שמירה בבסיס הנתונים
        user_doc = {
            "username": username,
            "password": hashed,  # שומרים את המוצפן בלבד!
            "created_at": datetime.now().isoformat()
        }
        db[COLLECTION_USERS].insert_one(user_doc)
        return True
    return False

def verify_user(username, password):
    if db is None: init_db()
    if db is not None:
        user = db[COLLECTION_USERS].find_one({"username": username})
        if not user:
            return False  # משתמש לא נמצא
            
        # בדיקה האם הסיסמה תואמת להצפנה
        return bcrypt.checkpw(password.encode('utf-8'), user['password'])
    return False

# --- לוגים ואירועים (ללא שינוי מהותי) ---
def log_event(event_type: str, data: dict):
    if db is None: init_db()
    if db is not None:
        event = {
            "event_type": event_type,
            "username": data.get("username", "anonymous"),
            "timestamp": datetime.now().isoformat(),
            "payload": data
        }
        try:
            db[COLLECTION_EVENTS].insert_one(event)
        except Exception as e:
            print(f"⚠️ Save Error: {e}")

def get_user_events(username: str):
    if db is None: init_db()
    if db is not None:
        query = {"username": username, "event_type": "TripGenerated"}
        return list(db[COLLECTION_EVENTS].find(query, {'_id': 0}).sort("timestamp", -1))
    return []