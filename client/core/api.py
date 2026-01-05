import requests

class APIService:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    # --- GENERIC METHODS ---
    def post(self, endpoint, data):
        """Generic POST request wrapper"""
        try:
            # Ensure endpoint starts with / 
            if not endpoint.startswith("/"):
                endpoint = f"/{endpoint}"
                
            url = f"{self.base_url}{endpoint}"
            print(f"📡 API POST: {url}")
            
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️ API Error {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Connection Exception: {e}")
            return None

    # --- AUTH METHODS ---
    def login(self, username, password):
        return self.post("/auth/login", {"username": username, "password": password}) or {"status": "error"}

    def register(self, username, password):
        return self.post("/auth/register", {"username": username, "password": password}) or {"status": "error"}

    # --- TRIP METHODS ---
    def generate_trip(self, payload):
        """Sends trip requirements to the backend"""
        return self.post("/trips/generate", payload)
    
    def get_weather(self, destination):
        # Return mock directly or call server
        return {"temp": 24, "desc": "Partly Cloudy", "icon": "⛅"}