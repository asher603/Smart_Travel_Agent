import requests

class APIService:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url

    def login(self, username, password):
        try:
            payload = {"username": username, "password": password}
            response = requests.post(f"{self.base_url}/login", json=payload, timeout=10)
            return response.json()
        except Exception as e:
            return {"error": f"Login Error: {str(e)}"}

    def generate_trip(self, username, destination, origin, stops, budget, currency, interest, days):
        try:
            payload = {
                "username": username,
                "destination": destination,
                "origin": origin,
                "stops": stops,
                "budget": budget,
                "currency": currency,
                "interest": interest,
                "duration": days
            }
            
            # --- השינוי כאן: timeout=600 ---
            # נותנים לו 10 דקות לחשוב לפני שמתייאשים
            response = requests.post(f"{self.base_url}/generate_trip", json=payload, timeout=600)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Server Error: {response.text}"}
        except Exception as e:
            return {"error": f"Connection Error: {str(e)}"}

    def get_history(self, username):
        try:
            response = requests.get(f"{self.base_url}/history/{username}", timeout=10)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            return []