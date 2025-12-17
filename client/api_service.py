import requests

class APIService:
    def __init__(self):
        # כתובת השרת המקומי שלך
        self.base_url = "http://127.0.0.1:8000"

    def get_trip_plan(self, destination):
        """
        שולח בקשה לשרת ומחזיר את תשובת ה-JSON
        """
        try:
            url = f"{self.base_url}/generate_trip/{destination}"
            response = requests.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Server returned status: {response.status_code}"}
                
        except requests.exceptions.ConnectionError:
            return {"error": "Connection failed. Is the server running?"}
        except Exception as e:
            return {"error": str(e)}