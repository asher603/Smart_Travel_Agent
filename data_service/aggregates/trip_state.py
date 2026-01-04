class TripAggregate:
    def __init__(self):
        self.trip_id = None
        self.username = None
        self.destination = None
        self.current_plan = {}
        self.chat_history = []

    def apply_events(self, events):
        for event in events:
            etype = event.get("event_type")
            data = event
            
            if etype == "TripCreated":
                self.trip_id = data["trip_id"]
                self.username = data["username"]
                self.destination = data["destination"]
            
            elif etype == "PlanGenerated":
                self.current_plan = data["plan_data"]
            
            elif etype == "ChatAdded":
                self.chat_history.append({
                    "message": data["message"],
                    "sender": data["sender"],
                    "timestamp": data["timestamp"]
                })
        return self

    def to_dict(self):
        return {
            "id": self.trip_id,
            "username": self.username,
            "destination": self.destination,
            "trip_plan": self.current_plan,
            "chat_history": self.chat_history
        }