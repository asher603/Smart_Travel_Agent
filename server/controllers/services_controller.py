from fastapi import APIRouter
from server.services.flight_service import flight_service
from server.services.weather_service import weather_service
from pydantic import BaseModel

router = APIRouter(prefix="/info", tags=["External Info"])

class FlightRequest(BaseModel):
    origin: str
    destination: str
    date: str

@router.post("/get_flights")
def get_flights(req: FlightRequest):
    return {"flights": flight_service.search_flights(req.origin, req.destination, req.date)}

@router.get("/get_weather")
def get_weather(city: str):
    desc, temp, icon = weather_service.get_current_weather(city)
    return {"desc": desc, "temp": temp, "icon": icon}