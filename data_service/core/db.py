import certifi
from pymongo import MongoClient
from data_service.core.config import settings

class Database:
    client: MongoClient = None

db_instance = Database()

def get_db():
    if db_instance.client is None:
        init_mongo()
    # FIX: Changed DB_NAME to DATABASE_NAME to match docker-compose environment variable
    return db_instance.client[settings.DATABASE_NAME]

def init_mongo():
    if not settings.MONGODB_URI:
        raise ValueError("MONGODB_URI not found in environment variables")

    # SECURITY: Print only the host part to avoid exposing password in logs
    masked_uri = settings.MONGODB_URI.split('@')[-1] if '@' in settings.MONGODB_URI else "HIDDEN"
    print(f"🔌 Connecting to MongoDB Atlas at: ...@{masked_uri}")

    try:
        # CRITICAL FIX for Docker + MongoDB Atlas:
        db_instance.client = MongoClient(
            settings.MONGODB_URI,
            tlsCAFile=certifi.where(),
            uuidRepresentation='standard'
        )
        
        # Test connection
        db_instance.client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas successfully!")
    except Exception as e:
        print(f"❌ MongoDB Connection Failed: {e}")
        raise e

def close_mongo():
    if db_instance.client:
        db_instance.client.close()
        print("🛑 MongoDB Connection Closed.")