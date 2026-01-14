from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Any, Dict
from data_service.events.store import EventStore
from data_service.events.models import TripCreated, PlanGenerated, ChatAdded
from data_service.aggregates.trip_state import TripAggregate
import uuid

router = APIRouter()
store = EventStore()

# --- מודל חדש לעדכון המצב ---
class StateUpdate(BaseModel):
    chat_history: List[Dict[str, Any]]

# --- WRITE (Commands) ---

@router.post("/events/create_trip")
def create_trip(payload: dict):
    trip_id = str(uuid.uuid4())
    event = TripCreated(
        trip_id=trip_id,
        username=payload["username"],
        destination=payload["destination"],
        initial_request=payload
    )
    store.append(event)
    return {"trip_id": trip_id}

@router.post("/events/add_plan")
def add_plan(payload: dict):
    event = PlanGenerated(
        trip_id=payload["trip_id"],
        plan_data=payload["plan_data"]
    )
    store.append(event)
    return {"status": "Plan saved"}

# --- READ (Queries) ---

@router.get("/trips/{trip_id}")
def get_trip_state(trip_id: str):
    # כאן אנחנו משנים גישה: במקום לנגן אירועים (Event Sourcing)
    # אנחנו קוראים ישירות מה-Snapshot, כי שם הצ'אט נשמר כרגע.
    
    trip = store.snapshots.find_one({"trip_id": trip_id})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # המרת ה-_id של מונגו למחרוזת
    if "_id" in trip:
        trip["_id"] = str(trip["_id"])
        
    return trip

@router.get("/user/{username}/summary")
def get_user_summary(username: str):
    trips = store.snapshots.find({"username": username})
    
    results = []
    for t in trips:
        results.append({
            "id": t["trip_id"],
            "destination": t["destination"],
            "date": t["created_at"],
            "budget": t.get("latest_plan", {}).get("budget", "?")
        })
    return results

# --- התיקון הגדול: Endpoint לעדכון ישיר ---
@router.put("/trips/{trip_id}/state")
def update_trip_state(trip_id: str, payload: StateUpdate):
    """
    Updates the chat history directly in the snapshot.
    Called by Server -> Client State Saver.
    """
    store.update_chat_history(trip_id, payload.chat_history)
    return {"status": "updated"}