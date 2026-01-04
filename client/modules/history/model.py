class HistoryModel:
    def __init__(self):
        self.username = ""
        self.trips = [] # List of dicts

    def remove_trip(self, trip_id):
        self.trips = [t for t in self.trips if t['id'] != trip_id]