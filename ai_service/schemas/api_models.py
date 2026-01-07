from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class TripRequest(BaseModel):
    destination: str
    origin: str
    duration: int
    budget: int
    currency: str = "USD"
    interest: str

class BudgetBreakdown(BaseModel):
    flights: int = Field(alias="Flights")
    accommodation: int = Field(alias="Accommodation")
    food: int = Field(alias="Food")
    activities: int = Field(alias="Activities")
    transport: int = Field(alias="Transport")

class DayActivity(BaseModel):
    day: int
    title: str
    activities: List[str]

class TripResponse(BaseModel):
    summary: str
    analyzed_vibe: str
    budget_breakdown: BudgetBreakdown
    itinerary: List[DayActivity]

# --- New Models for Chat & Refine ---
class ChatRequest(BaseModel):
    question: str
    context: str

class RefineRequest(BaseModel):
    trip_id: Optional[str] = None
    instructions: str
    current_plan: Dict[str, Any]