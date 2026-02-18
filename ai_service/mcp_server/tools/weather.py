"""
MCP Weather Tool — Open-Meteo API Integration
================================================
Fetches real-time weather data for any city worldwide.
Uses Open-Meteo's free Geocoding + Forecast APIs (no API key required).
"""

import httpx

# WMO Weather Interpretation Codes → Human-readable description + emoji
_WMO_CODES = {
    0: ("Clear Sky", "☀️"),
    1: ("Mainly Clear", "🌤️"),
    2: ("Partly Cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Depositing Rime Fog", "🌫️"),
    51: ("Light Drizzle", "🌦️"),
    53: ("Moderate Drizzle", "🌧️"),
    55: ("Dense Drizzle", "🌧️"),
    61: ("Slight Rain", "🌦️"),
    63: ("Moderate Rain", "🌧️"),
    65: ("Heavy Rain", "🌧️"),
    71: ("Slight Snow", "🌨️"),
    73: ("Moderate Snow", "❄️"),
    75: ("Heavy Snow", "❄️"),
    80: ("Slight Showers", "🌦️"),
    81: ("Moderate Showers", "🌧️"),
    82: ("Violent Showers", "⛈️"),
    95: ("Thunderstorm", "⛈️"),
}


def get_weather_tool(city: str) -> str:
    """
    Get current weather for a city using the Open-Meteo API.
    Returns a formatted string with temperature, condition, and wind speed.
    Free API — no authentication required.
    """
    try:
        # Step 1: Geocoding — resolve city name to coordinates
        geo_resp = httpx.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=5,
        )
        geo_data = geo_resp.json()

        if not geo_data.get("results"):
            return f"Could not find location '{city}'. Please use an English city name."

        location = geo_data["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]
        resolved_name = location.get("name", city)

        # Step 2: Forecast — coordinates to current weather
        weather_resp = httpx.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": "true",
                "timezone": "auto",
            },
            timeout=5,
        )
        weather_resp.raise_for_status()
        weather_data = weather_resp.json()

        if "current_weather" not in weather_data:
            return f"Weather data unavailable for {city}."

        current = weather_data["current_weather"]
        temp = current.get("temperature", "N/A")
        wind = current.get("windspeed", "N/A")
        code = current.get("weathercode", -1)

        description, emoji = _WMO_CODES.get(code, ("Unknown", "🌡️"))

        return (
            f"Weather in {resolved_name}: {emoji} {description}, "
            f"{temp}°C, Wind: {wind} km/h"
        )

    except httpx.TimeoutException:
        return f"Weather request timed out for {city}."
    except Exception as e:
        return f"Weather error for {city}: {str(e)}"