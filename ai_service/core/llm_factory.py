from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from ai_service.core.config import settings

class LLMFactory:
    """
    Factory to manage LLM providers with a 3-tier fallback strategy.
    """
    def __init__(self):
        self.google_key = settings.GOOGLE_API_KEY
        self.groq_key = settings.GROQ_API_KEY

    def _get_primary_model(self):
        """Tier 1: Google Gemini"""
        if not self.google_key:
            return self._get_backup_model()
        
        return ChatGoogleGenerativeAI(
            model=settings.PRIMARY_LLM_MODEL, 
            google_api_key=self.google_key,
            temperature=0.7
        )

    def _get_backup_model(self):
        """Tier 2: Groq (Llama via Cloud)"""
        if not self.groq_key:
            return self._get_local_model()
        
        return ChatGroq(
            temperature=0.7,
            model_name=settings.BACKUP_LLM_MODEL,
            api_key=self.groq_key
        )

    def _get_local_model(self):
        """Tier 3: Ollama (Local Docker Container)"""
        print(f"⚠️ Switching to Local Ollama Model: {settings.LOCAL_LLM_MODEL}")
        return ChatOllama(
            model=settings.LOCAL_LLM_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.7,
            timeout=300.0,    # תוספת: לחכות עד 5 דקות לטעינת מודל
            keep_alive="1h"   # תוספת: להשאיר את המודל בזיכרון לשעה
        )

    async def invoke(self, messages):
        """
        Executes the prompt with automatic fallback handling.
        """
        # Attempt 1: Google
        try:
            llm = self._get_primary_model()
            return await llm.ainvoke(messages)
        except Exception as e:
            print(f"🚨 Primary LLM (Google) Failed: {e}")
            
            # Attempt 2: Groq
            try:
                llm_backup = self._get_backup_model()
                return await llm_backup.ainvoke(messages)
            except Exception as e2:
                print(f"❌ Backup LLM (Groq) Failed: {e2}")
                
                # Attempt 3: Ollama (Local)
                try:
                    llm_local = self._get_local_model()
                    return await llm_local.ainvoke(messages)
                except Exception as e3:
                    print(f"💀 All LLMs Failed. Local Error: {e3}")
                    raise e3

    def get_llm(self):
        return self._get_primary_model()

llm_manager = LLMFactory()