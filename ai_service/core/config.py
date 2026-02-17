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
    
    N8N_WEBHOOK_URL: str = "http://n8n:5678/webhook/trip-action"
    
    # Model Configs
    PRIMARY_LLM_MODEL: str = "gemini-2.5-flash"
    BACKUP_LLM_MODEL: str = "llama-3.3-70b-versatile"
    
    # --- ADDED: Ollama Local Fallback ---
    # The hostname 'ollama' comes from the docker-compose service name
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    LOCAL_LLM_MODEL: str = "llama3.1"
    
    HF_VIBE_MODEL: str = "facebook/bart-large-mnli"
    HF_IMAGE_MODEL: str = "black-forest-labs/FLUX.1-schnell"
    HF_PROMPT_GUARD_MODEL: str = "meta-llama/Llama-Prompt-Guard-2-86M"
    PROMPT_GUARD_ML_ENABLED: bool = True
    PROMPT_GUARD_ML_THRESHOLD: float = 0.75

    class Config:
        # Tells Pydantic to read from .env file
        env_file = ".env"
        env_file_encoding = "utf-8"

# Singleton instance
settings = Settings()