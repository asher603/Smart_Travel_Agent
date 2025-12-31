import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

class LLMFactory:
    def __init__(self):
        self.google_key = os.getenv("GOOGLE_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")

    def _get_primary_model(self):
        """
        המודל הראשי: Gemini 2.5 Flash
        מודל מהיר, חכם ויציב (יוני 2025).
        """
        if not self.google_key:
            raise ValueError("Missing GOOGLE_API_KEY")
        
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",  # <--- המודל החדש והנכון
            google_api_key=self.google_key,
            temperature=0.7,
            convert_system_message_to_human=True
        )

    def _get_backup_model(self):
        """
        מודל הגיבוי: Groq (Llama 3)
        """
        if not self.groq_key:
            raise ValueError("Missing GROQ_API_KEY")
        
        print("⚠️ NOTE: Primary (Gemini) failed. Switching to Backup (Groq)...")
        
        return ChatGroq(
            temperature=0.7,
            model_name="llama-3.3-70b-versatile",
            api_key=self.groq_key
        )

    def invoke(self, messages):
        # ניסיון 1: Google Gemini 2.5
        try:
            llm = self._get_primary_model()
            return llm.invoke(messages)
            
        except Exception as e:
            print(f"🚨 Primary LLM (Gemini 2.5) Failed: {e}")
            print("🔄 Switching to Backup LLM (Groq)...")
            
            # ניסיון 2: Groq
            try:
                llm_backup = self._get_backup_model()
                return llm_backup.invoke(messages)

            except Exception as e2:
                print(f"❌ Backup LLM Failed too: {e2}")
                raise e2

llm_manager = LLMFactory()