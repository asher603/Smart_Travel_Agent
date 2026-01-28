from pymongo import MongoClient
from data_service.core.db import get_db
from data_service.events.models import BaseEvent

class EventStore:
    def __init__(self):
        self.db = get_db()
        self.collection = self.db["event_log"]
        self.snapshots = self.db["trip_snapshots"] # Optimization (Projections)

    def append(self, event: BaseEvent):
        """Save a new event to the log"""
        event_dict = event.dict()
        event_dict["_id"] = event.event_id
        self.collection.insert_one(event_dict)
        
        # PROJECTION: Update the read-optimized view immediately
        self._update_projection(event)

    def get_events(self, trip_id: str):
        """Get all events for a specific trip, sorted by time"""
        cursor = self.collection.find({"trip_id": trip_id}).sort("timestamp", 1)
        return list(cursor)

    def update_chat_history(self, trip_id: str, chat_history: list):
        """
        Directly updates the chat history in the snapshot.
        """
        self.snapshots.update_one(
            {"trip_id": trip_id},
            {"$set": {"chat_history": chat_history}}
        )

    def _update_projection(self, event):
        """
        Updates a 'current state' table so we don't have to replay 
        100 events every time we just want the dashboard list.
        """
        if event.event_type == "TripCreated":
            # 1. Extract the plan
            initial_plan = event.initial_request.get("generated_plan", {})
            current_status = "ready" if initial_plan else "planning"

            # 2. Build clean history - without preliminary text messages
            # The client can handle a list that starts directly with a plan
            initial_history = [
                {"type": "plan", "content": {"title": "Initial Plan", "plan": initial_plan}}
            ]

            # 3. Save to snapshot
            self.snapshots.insert_one({
                "trip_id": event.trip_id,
                "username": event.username,
                "destination": event.destination,
                "status": current_status,
                "created_at": event.timestamp,
                "latest_plan": initial_plan,
                "chat_history": initial_history 
            })
            
        elif event.event_type == "PlanGenerated":
            self.snapshots.update_one(
                {"trip_id": event.trip_id},
                {"$set": {"latest_plan": event.plan_data, "status": "ready"}}
            )