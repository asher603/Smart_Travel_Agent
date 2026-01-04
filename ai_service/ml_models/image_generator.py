import base64
from io import BytesIO
from huggingface_hub import InferenceClient
from ai_service.core.config import settings

HF_TOKEN = settings.HF_TOKEN

def generate_trip_image(destination: str, vibe: str) -> str:
    """Returns Base64 string of the image"""
    prompt = f"travel poster of {destination}, {vibe} theme, cinematic, 8k, vibrant"
    print(f"🎨 Generating Image: {prompt}")
    
    try:
        client = InferenceClient(api_key=HF_TOKEN)
        image = client.text_to_image(prompt=prompt, model="black-forest-labs/FLUX.1-schnell")
        
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"❌ Image Gen Failed: {e}")
        return None