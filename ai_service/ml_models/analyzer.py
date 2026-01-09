import json
from huggingface_hub import InferenceClient
from ai_service.core.config import settings

def analyze_user_vibe(interest_text: str) -> str:
    if not interest_text or len(interest_text.strip()) == 0:
        return "Standard"

    # Use settings
    if not settings.HF_TOKEN:
        print("⚠️ HF_TOKEN missing in settings.")
        return "General Tourism"

    try:
        client = InferenceClient(api_key=settings.HF_TOKEN)
        
        candidate_labels = [
            "Adventure & Nature", "Urban & Culture", "Relaxation & Spa", 
            "Food & Culinary", "Nightlife & Party", "History & Art", "Shopping"
        ]

        response = client(
            json={
                "inputs": interest_text,
                "parameters": {"candidate_labels": candidate_labels, "multi_label": False}
            },
            model=settings.HF_VIBE_MODEL
        )
        
        # Handle potential bytes response
        if isinstance(response, bytes):
            result = json.loads(response.decode("utf-8"))
        else:
            result = response
            
        return result['labels'][0]

    except Exception as e:
        print(f"⚠️ Vibe Analysis Failed: {e}")
        return "General Tourism"

def preload_vibe_model():
    """Smoke test for startup"""
    print("🧠 Preloading Vibe Model...")
    try:
        analyze_user_vibe("Test")
        print("✅ Vibe Model Connection: OK")
    except Exception as e:
        print(f"⚠️ Vibe Model Warning: {e}")