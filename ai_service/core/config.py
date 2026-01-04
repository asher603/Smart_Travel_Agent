import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "Smart Travel AI Service"
    VERSION: str = "2.5.0"
    DEBUG_MODE: bool = False
    
    # API Keys (Critical)
    GROQ_API_KEY: str
    GOOGLE_API_KEY: str
    HF_TOKEN: str

    # Model Configs
    PRIMARY_LLM_MODEL: str = "gemini-2.5-flash"
    BACKUP_LLM_MODEL: str = "llama-3.3-70b-versatile"
    HF_VIBE_MODEL: str = "facebook/bart-large-mnli"
    HF_IMAGE_MODEL: str = "black-forest-labs/FLUX.1-schnell"

    class Config:
        # Tells Pydantic to read from .env file
        env_file = ".env"
        env_file_encoding = "utf-8"

# Singleton instance
settings = Settings()