from fastapi import APIRouter, HTTPException
from data_service.events.store import EventStore
from data_service.events.models import TripCreated, PlanGenerated, ChatAdded
from data_service.aggregates.trip_state import TripAggregate
import uuid

router = APIRouter()
store = EventStore()

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

@router.post("/events/add_chat")
def add_chat(payload: dict):
    event = ChatAdded(
        trip_id=payload["trip_id"],
        message=payload["message"],
        sender=payload["sender"]
    )
    store.append(event)
    return {"status": "Message saved"}

# --- READ (Queries) ---

@router.get("/trips/{trip_id}")
def get_trip_state(trip_id: str):
    # 1. Fetch all raw events
    events = store.get_events(trip_id)
    if not events:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # 2. Replay them to build state
    aggregate = TripAggregate()
    aggregate.apply_events(events)
    
    return aggregate.to_dict()

@router.get("/user/{username}/summary")
def get_user_summary(username: str):
    # Query the 'Snapshot' (Projection) collection for speed
    # This avoids replaying 1000 events just to show a list
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