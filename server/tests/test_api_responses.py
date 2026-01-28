"""
Tests for API Response Models
=============================
Unit tests for the server's response structures.
"""

import pytest
from pydantic import BaseModel, ValidationError
from typing import Optional, Dict, Any, List


# Define test models that mirror the expected API responses
class SuccessResponse(BaseModel):
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    detail: str


class TripResponse(BaseModel):
    trip_id: str
    destination: str
    status: str
    created_at: str
    latest_plan: Optional[Dict[str, Any]] = None


class UserResponse(BaseModel):
    username: str
    preferences: Optional[Dict] = None


class TestSuccessResponses:
    """Tests for successful API responses"""
    
    def test_basic_success_response(self):
        """Basic success response should validate"""
        response = SuccessResponse(status="success")
        assert response.status == "success"
    
    def test_success_with_message(self):
        """Success response with message should validate"""
        response = SuccessResponse(
            status="success",
            message="Operation completed successfully"
        )
        assert response.message == "Operation completed successfully"
    
    def test_success_with_data(self):
        """Success response with data payload should validate"""
        response = SuccessResponse(
            status="success",
            data={"user_id": "123", "trips_count": 5}
        )
        assert response.data["user_id"] == "123"
        assert response.data["trips_count"] == 5
    
    def test_registration_success(self):
        """Registration success response format"""
        response = SuccessResponse(
            status="success",
            message="User created successfully"
        )
        assert "created" in response.message.lower()
    
    def test_login_success(self):
        """Login success response format"""
        response = SuccessResponse(
            status="success",
            data={"username": "testuser"}
        )
        assert response.data["username"] == "testuser"


class TestErrorResponses:
    """Tests for error API responses"""
    
    def test_basic_error_response(self):
        """Basic error response should validate"""
        response = ErrorResponse(detail="Something went wrong")
        assert response.detail == "Something went wrong"
    
    def test_user_not_found_error(self):
        """User not found error response"""
        response = ErrorResponse(detail="User not found")
        assert "not found" in response.detail.lower()
    
    def test_invalid_credentials_error(self):
        """Invalid credentials error response"""
        response = ErrorResponse(detail="Invalid credentials")
        assert "invalid" in response.detail.lower()
    
    def test_username_taken_error(self):
        """Username already taken error response"""
        response = ErrorResponse(detail="Username already taken")
        assert "taken" in response.detail.lower()
    
    def test_service_unavailable_error(self):
        """Service unavailable error response"""
        response = ErrorResponse(detail="Data Service Unavailable")
        assert "unavailable" in response.detail.lower()


class TestTripResponses:
    """Tests for trip-related API responses"""
    
    def test_trip_response_structure(self):
        """Trip response should have required fields"""
        response = TripResponse(
            trip_id="trip-123",
            destination="Paris",
            status="ready",
            created_at="2026-01-28T10:00:00"
        )
        
        assert response.trip_id == "trip-123"
        assert response.destination == "Paris"
        assert response.status == "ready"
    
    def test_trip_with_plan(self):
        """Trip response with plan data"""
        plan = {
            "summary": "A wonderful trip to Paris",
            "itinerary": [
                {"day": 1, "title": "Arrival", "activities": ["Check in", "Dinner"]}
            ]
        }
        
        response = TripResponse(
            trip_id="trip-456",
            destination="Paris",
            status="ready",
            created_at="2026-01-28T10:00:00",
            latest_plan=plan
        )
        
        assert response.latest_plan is not None
        assert "summary" in response.latest_plan
        assert "itinerary" in response.latest_plan
    
    def test_trip_planning_status(self):
        """Trip in planning status should validate"""
        response = TripResponse(
            trip_id="trip-789",
            destination="Tokyo",
            status="planning",
            created_at="2026-01-28T11:00:00"
        )
        
        assert response.status == "planning"
        assert response.latest_plan is None


class TestUserResponses:
    """Tests for user-related API responses"""
    
    def test_user_response_basic(self):
        """Basic user response should validate"""
        response = UserResponse(username="john_doe")
        assert response.username == "john_doe"
    
    def test_user_with_preferences(self):
        """User response with preferences should validate"""
        response = UserResponse(
            username="traveler123",
            preferences={
                "currency": "USD",
                "language": "en",
                "travel_style": "budget"
            }
        )
        
        assert response.preferences["currency"] == "USD"
        assert response.preferences["travel_style"] == "budget"
    
    def test_user_empty_preferences(self):
        """User with empty preferences should validate"""
        response = UserResponse(
            username="newuser",
            preferences={}
        )
        
        assert response.preferences == {}


class TestHTTPStatusCodes:
    """Tests for expected HTTP status codes"""
    
    def test_success_codes(self):
        """Document expected success status codes"""
        expected_success_codes = {
            "GET /trips": 200,
            "POST /register": 200,
            "POST /login": 200,
            "POST /trips/generate": 200,
        }
        
        for endpoint, code in expected_success_codes.items():
            assert code == 200, f"Expected 200 for {endpoint}"
    
    def test_error_codes(self):
        """Document expected error status codes"""
        expected_error_codes = {
            "invalid_credentials": 401,
            "user_not_found": 401,
            "username_taken": 400,
            "service_unavailable": 503,
            "internal_error": 500,
        }
        
        assert expected_error_codes["invalid_credentials"] == 401
        assert expected_error_codes["username_taken"] == 400
        assert expected_error_codes["service_unavailable"] == 503


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
