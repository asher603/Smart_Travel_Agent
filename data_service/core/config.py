import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Smart Travel Data Service (Event Store)"
    
    # Database Config
    # Priority: Env Var (Docker) -> .env file -> Default Value
    MONGODB_URI: str = "mongodb://localhost:27017" 
    DB_NAME: str = "smart_travel_events"
    
    # Collection Names (Constants)
    COLLECTION_EVENTS: str = "event_log"
    COLLECTION_SNAPSHOTS: str = "trip_snapshots"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # This prevents errors if .env is missing (common in Docker)
        extra = "ignore" 

settings = Settings()