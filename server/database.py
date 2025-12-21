import pymongo
import certifi
import os
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

CONNECTION_STRING = os.getenv("MONGODB_URI")
DB_NAME = "smart_travel_agent_db"
COLLECTION_NAME = "events"

client = None
db = None

def init_db():
    global client, db
    if not CONNECTION_STRING:
        print("❌ Error: MONGODB_URI not found in .env file")
        return

    try:
        client = pymongo.MongoClient(CONNECTION_STRING, tlsCAFile=certifi.where())
        db = client[DB_NAME]
        client.admin.command('ping')
        print("✅ MongoDB Connected!")
    except Exception as e:
        print(f"❌ MongoDB Error: {e}")

def log_event(event_type: str, data: dict):
    if db is None: init_db()
    
    # FIXED: Must use 'is not None' for pymongo objects
    if db is not None:
        username = data.get("username", "anonymous")
        event = {
            "event_type": event_type,
            "username": username,
            "timestamp": datetime.now().isoformat(),
            "payload": data
        }
        try:
            db[COLLECTION_NAME].insert_one(event)
            print(f"☁️ Saved: {event_type}")
        except Exception as e:
            print(f"⚠️ Save Error: {e}")

def get_user_events(username: str):
    if db is None: init_db()
    
    # FIXED: Must use 'is not None'
    if db is not None:
        # Get only completed trips for this user
        query = {"username": username, "event_type": "TripGenerated"}
        return list(db[COLLECTION_NAME].find(query, {'_id': 0}).sort("timestamp", -1))
    return []

def get_all_events():
    if db is None: init_db()
    
    # FIXED: Must use 'is not None'
    if db is not None:
        return list(db[COLLECTION_NAME].find({}, {'_id': 0}).sort("timestamp", -1))
    return []