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

    # --- הוספה חדשה: פונקציה לעדכון ישיר של הצ'אט ב-Snapshot ---
    def update_chat_history(self, trip_id: str, chat_history: list):
        """
        Directly updates the chat history in the snapshot.
        This bridges the gap between Client state and DB state.
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
            # 1. שליפת התוכנית (בדיוק כמו בקוד שעבד לך)
            initial_plan = event.initial_request.get("generated_plan", {})
            current_status = "ready" if initial_plan else "planning"

            # 2. בניית היסטוריה בפורמט שהקליינט שלך מצפה לו (type ו-content)
            req_data = event.initial_request.get("initial_request", {})
            
            # יצירת הודעת המשתמש (Text)
            user_text = f"I want a trip to {req_data.get('destination', 'Unknown')} from {req_data.get('origin', 'Unknown')}. Budget: {req_data.get('budget', '?')}."
            
            initial_history = [
                {"type": "text", "content": user_text, "is_user": True},
                {"type": "text", "content": "I have generated a trip plan for you!", "is_user": False},
                {"type": "plan", "content": {"title": "Initial Plan", "plan": initial_plan}}
            ]

            # 3. שמירה ל-Snapshot
            self.snapshots.insert_one({
                "trip_id": event.trip_id,
                "username": event.username,
                "destination": event.destination,
                "status": current_status,
                "created_at": event.timestamp,
                "latest_plan": initial_plan,
                "chat_history": initial_history  # עכשיו הקליינט יזהה את זה
            })
        elif event.event_type == "PlanGenerated":
            self.snapshots.update_one(
                {"trip_id": event.trip_id},
                {"$set": {"latest_plan": event.plan_data, "status": "ready"}}
            )
        # שים לב: ChatAdded כרגע לא מעדכן כאן כי אנחנו משתמשים בעדכון הישיר מה-Client