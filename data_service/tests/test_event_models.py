"""
Tests for Event Sourcing Models
===============================
Unit tests for the event models used in the Event Sourcing pattern.
"""

import pytest
from datetime import datetime
from data_service.events.models import (
    BaseEvent,
    TripCreated,
    PlanGenerated,
    ChatAdded
)


class TestBaseEvent:
    """Tests for BaseEvent model"""
    
    def test_event_id_auto_generated(self):
        """Event ID should be automatically generated"""
        event = BaseEvent(event_type="test")
        assert event.event_id is not None
        assert len(event.event_id) > 0
    
    def test_event_id_is_unique(self):
        """Each event should have a unique ID"""
        event1 = BaseEvent(event_type="test")
        event2 = BaseEvent(event_type="test")
        assert event1.event_id != event2.event_id
    
    def test_timestamp_auto_generated(self):
        """Timestamp should be automatically set"""
        event = BaseEvent(event_type="test")
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)
    
    def test_timestamp_is_recent(self):
        """Timestamp should be close to current time"""
        before = datetime.utcnow()
        event = BaseEvent(event_type="test")
        after = datetime.utcnow()
        
        assert before <= event.timestamp <= after
    
    def test_event_type_required(self):
        """Event type must be provided"""
        event = BaseEvent(event_type="CustomEvent")
        assert event.event_type == "CustomEvent"


class TestTripCreated:
    """Tests for TripCreated event"""
    
    def test_trip_created_event_type(self):
        """Event type should be 'TripCreated'"""
        event = TripCreated(
            trip_id="trip-123",
            username="testuser",
            destination="Paris",
            initial_request={"budget": 3000}
        )
        assert event.event_type == "TripCreated"
    
    def test_trip_created_fields(self):
        """All fields should be stored correctly"""
        event = TripCreated(
            trip_id="trip-456",
            username="john_doe",
            destination="Tokyo",
            initial_request={"budget": 5000, "duration": 7}
        )
        
        assert event.trip_id == "trip-456"
        assert event.username == "john_doe"
        assert event.destination == "Tokyo"
        assert event.initial_request["budget"] == 5000
        assert event.initial_request["duration"] == 7
    
    def test_trip_created_inherits_base(self):
        """Should inherit event_id and timestamp from BaseEvent"""
        event = TripCreated(
            trip_id="trip-789",
            username="user",
            destination="Rome",
            initial_request={}
        )
        
        assert event.event_id is not None
        assert event.timestamp is not None
    
    def test_trip_created_to_dict(self):
        """Should be serializable to dict"""
        event = TripCreated(
            trip_id="trip-001",
            username="alice",
            destination="Berlin",
            initial_request={"interests": ["museums", "food"]}
        )
        
        data = event.dict()
        assert "trip_id" in data
        assert "username" in data
        assert "destination" in data
        assert "initial_request" in data
        assert "event_id" in data
        assert "timestamp" in data
        assert "event_type" in data


class TestPlanGenerated:
    """Tests for PlanGenerated event"""
    
    def test_plan_generated_event_type(self):
        """Event type should be 'PlanGenerated'"""
        event = PlanGenerated(
            trip_id="trip-123",
            plan_data={"itinerary": []}
        )
        assert event.event_type == "PlanGenerated"
    
    def test_plan_generated_stores_plan(self):
        """Plan data should be stored correctly"""
        plan = {
            "summary": "Amazing trip to Paris",
            "itinerary": [
                {"day": 1, "title": "Arrival", "activities": ["Check-in", "Dinner"]}
            ],
            "budget_breakdown": {"flights": 500, "hotel": 800}
        }
        
        event = PlanGenerated(trip_id="trip-456", plan_data=plan)
        
        assert event.plan_data["summary"] == "Amazing trip to Paris"
        assert len(event.plan_data["itinerary"]) == 1
        assert event.plan_data["budget_breakdown"]["flights"] == 500
    
    def test_plan_generated_empty_plan(self):
        """Should handle empty plan data"""
        event = PlanGenerated(trip_id="trip-789", plan_data={})
        assert event.plan_data == {}


class TestChatAdded:
    """Tests for ChatAdded event"""
    
    def test_chat_added_event_type(self):
        """Event type should be 'ChatAdded'"""
        event = ChatAdded(
            trip_id="trip-123",
            message="Hello!",
            sender="user"
        )
        assert event.event_type == "ChatAdded"
    
    def test_chat_added_user_message(self):
        """Should store user messages correctly"""
        event = ChatAdded(
            trip_id="trip-456",
            message="Can you add more restaurants?",
            sender="user"
        )
        
        assert event.message == "Can you add more restaurants?"
        assert event.sender == "user"
    
    def test_chat_added_ai_message(self):
        """Should store AI messages correctly"""
        event = ChatAdded(
            trip_id="trip-789",
            message="I've added 3 more restaurants to your itinerary.",
            sender="ai"
        )
        
        assert event.sender == "ai"
        assert "restaurants" in event.message
    
    def test_chat_added_hebrew_message(self):
        """Should handle Hebrew messages"""
        event = ChatAdded(
            trip_id="trip-001",
            message="אני רוצה להוסיף עוד מסעדות",
            sender="user"
        )
        
        assert "מסעדות" in event.message


class TestEventSerialization:
    """Tests for event serialization/deserialization"""
    
    def test_trip_created_json_compatible(self):
        """TripCreated should be JSON serializable"""
        import json
        
        event = TripCreated(
            trip_id="trip-json-test",
            username="test",
            destination="Paris",
            initial_request={"test": True}
        )
        
        data = event.dict()
        # Convert datetime to string for JSON
        data["timestamp"] = data["timestamp"].isoformat()
        
        json_str = json.dumps(data)
        loaded = json.loads(json_str)
        
        assert loaded["trip_id"] == "trip-json-test"
        assert loaded["destination"] == "Paris"
    
    def test_all_events_have_common_fields(self):
        """All event types should have common base fields"""
        events = [
            TripCreated(trip_id="1", username="u", destination="d", initial_request={}),
            PlanGenerated(trip_id="2", plan_data={}),
            ChatAdded(trip_id="3", message="m", sender="user")
        ]
        
        for event in events:
            assert hasattr(event, "event_id")
            assert hasattr(event, "timestamp")
            assert hasattr(event, "event_type")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
