from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from ai_service.core.config import settings

class LLMFactory:
    def __init__(self):
        self.google_key = settings.GOOGLE_API_KEY
        self.groq_key = settings.GROQ_API_KEY

    def _get_primary_model(self):
        if not self.google_key:
            # Fallback if primary key is missing
            return self._get_backup_model()
        
        return ChatGoogleGenerativeAI(
            model=settings.PRIMARY_LLM_MODEL, 
            google_api_key=self.google_key,
            temperature=0.7,
            convert_system_message_to_human=True
        )

    def _get_backup_model(self):
        if not self.groq_key:
            raise ValueError("Missing both GOOGLE_API_KEY and GROQ_API_KEY")
        
        return ChatGroq(
            temperature=0.7,
            model_name=settings.BACKUP_LLM_MODEL,
            api_key=self.groq_key
        )

    def invoke(self, messages):
        try:
            llm = self._get_primary_model()
            return llm.invoke(messages)
        except Exception as e:
            print(f"🚨 Primary LLM Failed: {e}")
            try:
                llm_backup = self._get_backup_model()
                return llm_backup.invoke(messages)
            except Exception as e2:
                print(f"❌ Backup LLM Failed: {e2}")
                raise e2

    def get_llm(self):
        """Returns the raw LangChain object"""
        return self._get_primary_model()

# This creates the singleton instance that other files are trying to import
llm_manager = LLMFactory()