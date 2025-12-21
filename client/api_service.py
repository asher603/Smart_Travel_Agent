import requests

class APIService:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"

    def login(self, username, password):
        try:
            payload = {"username": username, "password": password}
            response = requests.post(f"{self.base_url}/login", json=payload)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def generate_trip(self, username, destination, budget, interest, days):
        try:
            payload = {
                "username": username,
                "destination": destination,
                "budget": budget,
                "interest": interest,
                "days": days
            }
            response = requests.post(f"{self.base_url}/generate_trip", json=payload)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Server Error: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def get_history(self, username):
        try:
            response = requests.get(f"{self.base_url}/history/{username}")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            return [{"error": str(e)}]