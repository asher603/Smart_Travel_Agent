import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Keys
    AMADEUS_API_KEY: str
    AMADEUS_SECRET: str
    
    # Service URLs
    AI_SERVICE_URL: str = "http://localhost:8002"
    DATA_SERVICE_URL: str = "http://localhost:8004"

    class Config:
        env_file = ".env"

settings = Settings()