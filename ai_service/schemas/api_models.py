from pydantic import BaseModel, Field
from typing import List, Optional

class TripRequest(BaseModel):
    destination: str
    origin: str
    duration: int
    budget: int
    currency: str = "USD"
    interest: str  # User's raw text (e.g., "I love spicy food and history")

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
    analyzed_vibe: str  # <--- Added by Hugging Face
    budget_breakdown: BudgetBreakdown
    itinerary: List[DayActivity]