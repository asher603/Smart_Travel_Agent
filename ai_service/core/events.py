from fastapi import FastAPI
from contextlib import asynccontextmanager
from ai_service.core.config import settings
from ai_service.core.llm_factory import LLMFactory
from ai_service.ml_models.analyzer import preload_vibe_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    print(f"🚀 {settings.APP_NAME} v{settings.VERSION} is starting up...")
    
    # 1. Validate Keys
    if not settings.HF_TOKEN:
        print("⚠️ WARNING: HF_TOKEN is missing. Image generation will fail.")
    
    # 2. Pre-load Models (Optional but recommended)
    # This 'wakes up' the connection to the LLM and HF so the first request is fast.
    try:
        print("🧠 Warming up LLM Factory...")
        llm = LLMFactory.get_llm()
        # You could run a dummy invocation here if you wanted to test connection
        # await llm.ainvoke("Ping") 
        print(f"✅ LLM Ready: {settings.PRIMARY_LLM_MODEL}")
    except Exception as e:
        print(f"❌ LLM Init Failed: {e}")

    yield # The application runs here

    # --- SHUTDOWN LOGIC ---
    print("🛑 Shutting down AI Service...")
    # Close DB connections or HTTP sessions here if you had them.