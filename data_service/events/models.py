from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

class BaseEvent(BaseModel):
    # התיקון: שימוש ב-default_factory מבטיח מזהה ייחודי לכל אירוע מחדש
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    # כנ"ל לגבי הזמן - שיהיה מדויק לרגע היצירה ולא לרגע עליית השרת
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str

class TripCreated(BaseEvent):
    event_type: str = "TripCreated"
    trip_id: str
    username: str
    destination: str
    initial_request: Dict[str, Any]

class PlanGenerated(BaseEvent):
    event_type: str = "PlanGenerated"
    trip_id: str
    plan_data: Dict[str, Any] # The full JSON from AI

class ChatAdded(BaseEvent):
    event_type: str = "ChatAdded"
    trip_id: str
    message: str
    sender: str # "user" or "ai"

# Union type for easy handling
EventPayload = TripCreated | PlanGenerated | ChatAdded