import requests

class APIService:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"

    def check_connection(self):
        try:
            response = requests.get(f"{self.base_url}/")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            return {"error": str(e)}
        return {"error": "Failed to connect"}

    def get_trip_plan(self, destination):
        try:
            response = requests.get(f"{self.base_url}/generate_trip/{destination}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            return {"error": str(e)}