import requests

class APIService:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def login(self, username, password):
        """Sends login request to Gateway -> App Server"""
        try:
            url = f"{self.base_url}/auth/login"
            response = requests.post(url, json={"username": username, "password": password})

            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "detail": response.text}
        except Exception as e:
            print(f"API Error: {e}")
            return {"status": "error", "detail": str(e)}

    def register(self, username, password):
        """Sends register request to Gateway -> App Server"""
        try:
            url = f"{self.base_url}/auth/register"
            response = requests.post(url, json={"username": username, "password": password})
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "detail": response.text}
        except Exception as e:
            return {"status": "error", "detail": str(e)}