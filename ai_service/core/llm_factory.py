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
            timeout=300.0,    # Wait up to 5 minutes for model loading
            keep_alive="1h"   # Keep model in memory for 1 hour
        )

    async def invoke(self, messages, preferred_model="gemini"):
        """
        Executes with fallback starting from the preferred model.
        Order: Gemini -> Groq -> Ollama
        """
        model_key = preferred_model.lower()
        
        # Priority Chain
        chain = ["gemini", "groq", "ollama"]
        
        # Determine starting point
        if model_key in chain:
            start_index = chain.index(model_key)
        else:
            start_index = 0 # Default to Gemini

        errors = []

        # Iterate from the selected model downwards
        for i in range(start_index, len(chain)):
            current_stage = chain[i]
            
            try:
                if current_stage == "gemini":
                    print("🤖 Using Model: Google Gemini")
                    llm = self._get_primary_model()
                elif current_stage == "groq":
                    print("⚡ Using Model: Groq Llama")
                    llm = self._get_backup_model()
                else:
                    print("🦙 Using Model: Local Ollama")
                    llm = self._get_local_model()

                return await llm.ainvoke(messages)

            except Exception as e:
                print(f"❌ {current_stage.capitalize()} Failed: {e}")
                errors.append(f"{current_stage}: {e}")
                # Continue to next model in loop
        
        raise Exception(f"All models failed. Errors: {errors}")

    def get_llm(self):
        return self._get_primary_model()

llm_manager = LLMFactory()