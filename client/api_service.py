import requests

class APIService:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url

    # --- פונקציה גנרית חדשה (חובה עבור יצירת התמונה) ---
    def post(self, endpoint, data, timeout=60):
        """
        פונקציה מרכזית לשליחת בקשות POST.
        מטפלת בשגיאות, בכתובת המלאה וב-Timeout.
        """
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.post(url, json=data, timeout=timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                # נסיון לחלץ הודעת שגיאה מפורטת מהשרת
                try:
                    error_detail = response.json().get("detail", response.text)
                    return {"error": error_detail}
                except:
                    return {"error": f"Server Error {response.status_code}"}
                    
        except requests.exceptions.Timeout:
            return {"error": "Connection timed out. Server is busy."}
        except Exception as e:
            return {"error": f"Connection Error: {str(e)}"}

    # --- פונקציות ספציפיות (מעודכנות) ---

    def login(self, username, password):
        return self.post("/login", {"username": username, "password": password}, timeout=30)

    def register(self, username, password):
        return self.post("/register", {"username": username, "password": password}, timeout=30)

    def generate_trip(self, username, destination, origin, stops, budget, currency, interest, days):
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
        # Timeout ארוך מאוד (10 דקות) ליצירת הטיול
        return self.post("/generate_trip", payload, timeout=600)

    def get_history(self, username):
        try:
            response = requests.get(f"{self.base_url}/history/{username}", timeout=30)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception:
            return []