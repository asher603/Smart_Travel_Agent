class HistoryModel:
    def get_history(self, api_service, username):
        """Fetches list of trips for user"""
        try:
            # We assume your API expects 'username' in json body
            response = api_service.post("/trips/history", {"username": username})
            return response.get("trips", []) if response else []
        except Exception as e:
            print(f"History Model Error: {e}")
            return []

    def get_trip_details(self, api_service, trip_id):
        """Fetches full details for a specific trip"""
        try:
            response = api_service.post("/trips/details", {"trip_id": trip_id})
            return response.get("trip") if response else None
        except Exception as e:
            print(f"Trip Details Error: {e}")
            return None

    def delete_trip(self, api_service, trip_id):
        """Deletes a trip"""
        try:
            response = api_service.post("/trips/delete", {"trip_id": trip_id})
            return response and response.get("status") == "success"
        except Exception as e:
            print(f"Delete Error: {e}")
            return False