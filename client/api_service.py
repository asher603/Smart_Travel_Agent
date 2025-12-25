import requests

class APIService:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url

    def login(self, username, password):
        try:
            payload = {"username": username, "password": password}
            # Timeout של 30 שניות
            response = requests.post(f"{self.base_url}/login", json=payload, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "Invalid username or password"}
        except Exception as e:
            return {"error": f"Login Error: {str(e)}"}

    def register(self, username, password):
        try:
            payload = {"username": username, "password": password}
            response = requests.post(f"{self.base_url}/register", json=payload, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                # מחזיר את הודעת השגיאה הספציפית מהשרת (כגון 'Username exists')
                try:
                    return {"error": response.json().get("detail", "Registration failed")}
                except:
                    return {"error": f"Error {response.status_code}"}
        except Exception as e:
            return {"error": f"Connection Error: {str(e)}"}

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
            # Timeout ארוך ל-AI (10 דקות)
            response = requests.post(f"{self.base_url}/generate_trip", json=payload, timeout=600)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Server Error: {response.text}"}
        except Exception as e:
            return {"error": f"Connection Error: {str(e)}"}

    def get_history(self, username):
        try:
            response = requests.get(f"{self.base_url}/history/{username}", timeout=30)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            return []