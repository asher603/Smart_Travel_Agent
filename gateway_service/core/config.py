import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Gateway Configuration.
    Loads environment variables defined in docker-compose.yml.
    """
    APP_NAME: str = "Smart Travel Gateway"

    # Service URLs (Defaults match the Docker Compose service names)
    # The Gateway uses these URLs to forward requests to the correct internal service.
    SERVER_URL: str = os.getenv("SERVER_URL", "http://server:8001")
    AI_SERVICE_URL: str = os.getenv("AI_SERVICE_URL", "http://ai_service:8002")
    DATA_SERVICE_URL: str = os.getenv("DATA_SERVICE_URL", "http://data_service:8003")

    class Config:
        case_sensitive = True
        # Optional: Load from .env file for local development
        env_file = ".env"

settings = Settings()