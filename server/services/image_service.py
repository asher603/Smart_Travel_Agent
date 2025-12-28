import os
import base64
from io import BytesIO
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

def generate_trip_image(destination, interest):
    print(f"🎨 Generating Image: {destination}")
    image_prompt = f"travel poster of {destination}"
    if interest:
        image_prompt += f", {interest} theme"
    image_prompt += ", cinematic, 8k, vibrant."
    
    try:
        client = InferenceClient(api_key=HF_TOKEN)
        # שימוש במודל FLUX המהיר
        image = client.text_to_image(prompt=image_prompt, model="black-forest-labs/FLUX.1-schnell")
        
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return {"image_base64": img_str}
    except Exception as e:
        print(f"❌ Image Service Error: {e}")
        return {"image_base64": None}