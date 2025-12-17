from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class TravelAgent:
    def __init__(self):
        # אתחול המודל - וודא שמותקן אצלך llama3 או llama2 ב-Ollama
        # אם יש לך מודל אחר, שנה את השם כאן
        self.llm = Ollama(model="llama3.2")

        # הגדרת התבנית (Prompt)
        self.prompt = PromptTemplate(
            template="""
            You are an expert travel agent.
            Please create a detailed 3-day itinerary for a trip to: {destination}.
            Include main attractions, local food recommendations, and travel tips.
            Provide the answer in a clear, structured format.
            """,
            input_variables=["destination"]
        )

        # יצירת השרשרת (Chain) בשיטה החדשה (LCEL - LangChain Expression Language)
        # זה מחבר את: הפרומפט -> המודל -> מפענח הטקסט
        self.chain = self.prompt | self.llm | StrOutputParser()

    def generate_response(self, destination: str):
        """
        מקבל יעד ומחזיר את המסלול שהמודל יצר
        """
        try:
            response = self.chain.invoke({"destination": destination})
            return {"trip_plan": response}
        except Exception as e:
            return {"error": str(e)}

# בדיקה קטנה שאפשר להריץ ישירות את הקובץ הזה כדי לראות שהוא עובד
if __name__ == "__main__":
    agent = TravelAgent()
    print("Testing Agent...")
    print(agent.generate_response("Paris"))