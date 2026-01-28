from fastmcp import FastMCP
from ai_service.mcp_server.tools.flights import search_flights_tool
from ai_service.mcp_server.tools.weather import get_weather_tool

# 1. Create the MCP server instance
mcp = FastMCP("Travel Agent Tools")

# 2. Define tools
@mcp.tool()
def search_flights(origin: str, destination: str, date: str) -> str:
    """Search for flights between cities."""
    return search_flights_tool(origin, destination, date)

@mcp.tool()
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return get_weather_tool(city)

# Note: Do not write app = ... here
# The fastmcp run command handles that automatically