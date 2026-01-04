from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

class BaseEvent(BaseModel):
    event_id: str = str(uuid.uuid4())
    timestamp: datetime = datetime.utcnow()
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