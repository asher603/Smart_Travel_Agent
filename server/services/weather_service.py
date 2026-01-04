import requests
from typing import Tuple

class WeatherService:
    def get_current_weather(self, city: str) -> Tuple[str, float, str]:
        """
        Retrieves current weather for a specific city name.
        Returns: (Description, Temperature, Icon)
        """
        try:
            # 1. Get Coordinates for the city (Geocoding)
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
            geo_res = requests.get(geo_url, timeout=5)
            geo_data = geo_res.json()

            if not geo_data.get('results'):
                return ("Unknown Location", 0.0, "❓")

            location = geo_data['results'][0]
            lat = location['latitude']
            lon = location['longitude']

            # 2. Fetch Weather from Open-Meteo
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
            response = requests.get(weather_url, timeout=5)
            response.raise_for_status()
            data = response.json()

            if 'current_weather' in data:
                return self._parse_weather(data['current_weather'])

        except Exception as e:
            print(f"Weather Fetch Error: {e}")

        # Fallback in case of error
        return ("", 0.0, "weather_error.png")

    def _parse_weather(self, weather_data: dict) -> Tuple[str, float, str]:
        """
        Parses WMO codes to text and emoji (Based on your C# logic).
        """
        code = weather_data.get('weathercode', -1)
        temp = weather_data.get('temperature', 0.0)

        # Weather Status Mapping
        if code == 0:
            return "Clear", temp, "☀️"
        elif code in [1, 2, 3]:
            return "Partly Cloudy", temp, "⛅"
        elif code in [45, 48]:
            return "Fog", temp, "🌫️"
        elif code in [51, 53, 55]:
            return "Drizzle", temp, "🌧️"
        elif code in [61, 63, 65]:
            return "Rainy", temp, "🌧️"
        
        return "Cloudy", temp, "🌧️"

# Create a singleton instance
weather_service = WeatherService()