from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class TripResponse(BaseModel):
    trip_plan: Dict[str, Any]
    status: str
    message: Optional[str] = None