from fastapi import FastAPI
from contextlib import asynccontextmanager
from ai_service.core.config import settings
# שים לב: Import למופע (instance) ולא למחלקה
from ai_service.core.llm_factory import llm_manager 
from ai_service.ml_models.analyzer import preload_vibe_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    print(f"🚀 {settings.APP_NAME} is starting up...")
    
    # 1. Validate Keys
    if not settings.HF_TOKEN:
        print("⚠️ WARNING: HF_TOKEN is missing. Image generation will fail.")
    
    # 2. Pre-load Models
    try:
        print("🧠 Warming up LLM Factory...")
        # התיקון הקריטי: קריאה לפונקציה מתוך המופע
        llm = llm_manager.get_llm() 
        print(f"✅ LLM Manager initialized.")
    except Exception as e:
        print(f"❌ LLM Init Failed: {e}")

    yield # The application runs here

    # --- SHUTDOWN LOGIC ---
    print("🛑 Shutting down AI Service...")