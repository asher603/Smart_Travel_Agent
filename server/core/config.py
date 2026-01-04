import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Keys
    AMADEUS_API_KEY: str
    AMADEUS_SECRET: str
    
    # Service URLs
    DATA_SERVICE_URL: str = "http://localhost:8002"
    AI_SERVICE_URL: str = "http://localhost:8001"

    class Config:
        env_file = ".env"

settings = Settings()