from pymongo import MongoClient
from data_service.core.config import settings

class Database:
    client: MongoClient = None

db_instance = Database()

def get_db():
    if db_instance.client is None:
        init_mongo()
    return db_instance.client[settings.DB_NAME]

def init_mongo():
    if not settings.MONGODB_URI:
        raise ValueError("MONGODB_URI not found in environment variables")

    print(f"🔌 Connecting to MongoDB at {settings.MONGODB_URI} ...")
    try:
        # FORCE TLS OFF: This is the critical fix for local Docker
        db_instance.client = MongoClient(
            settings.MONGODB_URI,
            tls=False,  
            uuidRepresentation='standard'
        )
        
        # Test connection
        db_instance.client.admin.command('ping')
        print("✅ Connected to Event Store!")
    except Exception as e:
        print(f"❌ MongoDB Connection Failed: {e}")
        raise e

def close_mongo():
    if db_instance.client:
        db_instance.client.close()
        print("🛑 MongoDB Connection Closed.")