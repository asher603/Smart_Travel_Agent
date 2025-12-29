import pymongo
import certifi
import os
import bcrypt
from datetime import datetime
from bson.objectid import ObjectId
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

CONNECTION_STRING = os.getenv("MONGODB_URI")
DB_NAME = "smart_travel_agent_db"
COLLECTION_USERS = "users"
COLLECTION_TRIPS = "trips"  # קולקציה ייעודית לטיולים מלאים

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
        client.admin.command('ping')
        print("✅ MongoDB Connected!")
    except Exception as e:
        print(f"❌ MongoDB Error: {e}")

# --- משתמשים ---
def create_user(username, password):
    if db is None: init_db()
    if db is not None:
        if db[COLLECTION_USERS].find_one({"username": username}):
            return False
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user_doc = {
            "username": username,
            "password": hashed,
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
            return False
        return bcrypt.checkpw(password.encode('utf-8'), user['password'])
    return False

# --- ניהול טיולים מלאים ---

def create_new_trip(username, initial_data):
    """יוצר מסמך טיול חדש ומחזיר את ה-ID שלו"""
    if db is None: init_db()
    if db is not None:
        trip_doc = {
            "username": username,
            "destination": initial_data.get("destination", "Unknown"),
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "trip_data": initial_data, # המידע הגולמי (תקציב, ימים וכו')
            "chat_history": [] # כאן יישמר כל הצ'אט
        }
        result = db[COLLECTION_TRIPS].insert_one(trip_doc)
        return str(result.inserted_id)
    return None

def update_trip_history(trip_id, chat_history):
    """מעדכן את היסטוריית הצ'אט של טיול קיים"""
    if db is None: init_db()
    if db is not None:
        try:
            db[COLLECTION_TRIPS].update_one(
                {"_id": ObjectId(trip_id)},
                {
                    "$set": {
                        "chat_history": chat_history,
                        "last_updated": datetime.now().isoformat()
                    }
                }
            )
            return True
        except Exception as e:
            print(f"Update Error: {e}")
    return False

def get_user_trips_summary(username):
    """מחזיר רשימה מקוצרת של טיולים להיסטוריה"""
    if db is None: init_db()
    if db is not None:
        # שולף רק שדות רלוונטיים לתצוגה ברשימה
        cursor = db[COLLECTION_TRIPS].find(
            {"username": username},
            {"_id": 1, "destination": 1, "created_at": 1, "trip_data.budget": 1}
        ).sort("last_updated", -1)
        
        results = []
        for doc in cursor:
            results.append({
                "id": str(doc["_id"]),
                "destination": doc.get("destination"),
                "date": doc.get("created_at"),
                "budget": doc.get("trip_data", {}).get("budget", "?")
            })
        return results
    return []

def get_full_trip(trip_id):
    """שולף את כל המידע על הטיול כדי לשחזר אותו"""
    if db is None: init_db()
    if db is not None:
        try:
            doc = db[COLLECTION_TRIPS].find_one({"_id": ObjectId(trip_id)})
            if doc:
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                return doc
        except:
            pass
    return None