import requests
from typing import Tuple

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
    
    # --- WEATHER SERVICE (Integrated) ---
    def get_weather(self, city: str) -> dict:
        """
        Retrieves real weather from Open-Meteo.
        Returns dict matching UI expectation: {"desc": str, "temp": float, "icon": str}
        """
        try:
            # 1. Geocoding
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
            geo_res = requests.get(geo_url, timeout=5)
            geo_data = geo_res.json()

            if not geo_data.get('results'):
                return {"desc": "Unknown", "temp": 0.0, "icon": "❓"}

            location = geo_data['results'][0]
            lat = location['latitude']
            lon = location['longitude']

            # 2. Forecast
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
            response = requests.get(weather_url, timeout=5)
            response.raise_for_status()
            data = response.json()

            if 'current_weather' in data:
                desc, temp, icon = self._parse_weather_code(data['current_weather'])
                return {"desc": desc, "temp": temp, "icon": icon}

        except Exception as e:
            print(f"Weather Fetch Error: {e}")

        return {"desc": "Unavailable", "temp": 0.0, "icon": "⚠️"}

    def _parse_weather_code(self, weather_data: dict) -> Tuple[str, float, str]:
        """Parses WMO codes to text and emoji"""
        code = weather_data.get('weathercode', -1)
        temp = weather_data.get('temperature', 0.0)

        if code == 0:
            return "Clear", temp, "☀️"
        elif code in [1, 2, 3]:
            return "Partly Cloudy", temp, "⛅"
        elif code in [45, 48]:
            return "Fog", temp, "🌫️"
        elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
            return "Rainy", temp, "🌧️"
        elif code in [71, 73, 75, 77, 85, 86]:
            return "Snow", temp, "❄️"
        elif code in [95, 96, 99]:
            return "Storm", temp, "⚡"
        
        return "Cloudy", temp, "☁️"