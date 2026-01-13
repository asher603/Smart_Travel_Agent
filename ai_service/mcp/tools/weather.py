import random

def get_weather_tool(city: str) -> str:
    conditions = ["Sunny", "Cloudy", "Rainy"]
    temp = random.randint(15, 30)
    return f"The weather in {city} is {random.choice(conditions)} with {temp}°C."