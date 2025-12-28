import os
import json
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

# טעינת משתני הסביבה (בשביל הטוקן)
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

def analyze_user_vibe(interest_text: str) -> str:
    """
    מבצע ניתוח טקסט (Zero-Shot Classification) באמצעות Hugging Face.
    מממש את דרישה מס' 8 בפרויקט: "שימוש במודל ניתוח".
    
    המטרה: לקחת את מה שהמשתמש אוהב, ולהבין מה ה"וייב" של הטיול.
    """
    
    # אם המשתמש לא כתב כלום, נחזיר ערך דיפולטיבי
    if not interest_text or len(interest_text.strip()) == 0:
        return "Standard"

    print(f"🧠 Analysis Service: Analyzing vibe for '{interest_text}'...")

    try:
        client = InferenceClient(api_key=HF_TOKEN)
        
        # הגדרת הקטגוריות האפשריות לטיול
        candidate_labels = [
            "Adventure & Nature", 
            "Urban & Culture", 
            "Relaxation & Spa", 
            "Food & Culinary", 
            "Nightlife & Party",
            "History & Art",
            "Shopping & Fashion"
        ]

        # שליחה למודל BART (מודל מצוין לסיווג טקסט ללא אימון מוקדם)
        response = client.post(
            json={
                "inputs": interest_text,
                "parameters": {
                    "candidate_labels": candidate_labels,
                    "multi_label": False
                }
            },
            model="facebook/bart-large-mnli"
        )
        
        # פענוח התשובה (המודל מחזיר Bytes שצריך להפוך ל-JSON)
        result = json.loads(response.decode("utf-8"))
        
        # שליפת התווית עם הציון הגבוה ביותר
        top_label = result['labels'][0]
        confidence = result['scores'][0]

        print(f"✅ Analysis Result: {top_label} (Confidence: {confidence:.2f})")
        return top_label

    except Exception as e:
        print(f"⚠️ Analysis Service Error: {e}")
        # במקרה של תקלה (למשל אין אינטרנט או טוקן שגוי), נחזיר ערך בטוח
        return "General Tourism"