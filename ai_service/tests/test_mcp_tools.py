"""
Tests for MCP Tools
===================
Unit tests for the MCP server tools (flights and weather).
"""

import pytest
from ai_service.mcp_server.tools.flights import search_flights_tool
from ai_service.mcp_server.tools.weather import get_weather_tool


class TestFlightsTool:
    """Tests for the flights search tool"""
    
    def test_search_flights_returns_string(self):
        """Tool should return a string response"""
        result = search_flights_tool("Tel Aviv", "Paris", "2026-03-15")
        assert isinstance(result, str)
    
    def test_search_flights_contains_origin(self):
        """Response should include the origin city"""
        result = search_flights_tool("New York", "London", "2026-04-01")
        assert "New York" in result
    
    def test_search_flights_contains_destination(self):
        """Response should include the destination city"""
        result = search_flights_tool("Berlin", "Tokyo", "2026-05-20")
        assert "Tokyo" in result
    
    def test_search_flights_contains_date(self):
        """Response should include the search date"""
        result = search_flights_tool("Rome", "Madrid", "2026-06-10")
        assert "2026-06-10" in result
    
    def test_search_flights_contains_options(self):
        """Response should contain flight options"""
        result = search_flights_tool("Tel Aviv", "Athens", "2026-07-01")
        # Should have numbered options (1., 2., etc.)
        assert "1." in result
    
    def test_search_flights_hebrew_cities(self):
        """Tool should handle Hebrew city names"""
        result = search_flights_tool("תל אביב", "פריז", "2026-08-15")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_search_flights_special_characters(self):
        """Tool should handle special characters in city names"""
        result = search_flights_tool("São Paulo", "México City", "2026-09-01")
        assert isinstance(result, str)


class TestWeatherTool:
    """Tests for the weather tool"""
    
    def test_get_weather_returns_string(self):
        """Tool should return a string response"""
        result = get_weather_tool("Paris")
        assert isinstance(result, str)
    
    def test_get_weather_contains_city(self):
        """Response should include the city name"""
        result = get_weather_tool("Tokyo")
        assert "Tokyo" in result
    
    def test_get_weather_contains_temperature(self):
        """Response should include temperature"""
        result = get_weather_tool("London")
        assert "°C" in result
    
    def test_get_weather_contains_condition(self):
        """Response should include weather condition"""
        result = get_weather_tool("Rome")
        # Should contain one of the conditions
        conditions = ["Sunny", "Cloudy", "Rainy"]
        assert any(cond in result for cond in conditions)
    
    def test_get_weather_hebrew_city(self):
        """Tool should handle Hebrew city names"""
        result = get_weather_tool("ירושלים")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_get_weather_multiple_calls_vary(self):
        """Weather should potentially vary between calls (randomness)"""
        # Call multiple times and check we get valid responses each time
        results = [get_weather_tool("Berlin") for _ in range(5)]
        assert all(isinstance(r, str) for r in results)
        assert all("Berlin" in r for r in results)


class TestMCPToolsIntegration:
    """Integration tests for MCP tools working together"""
    
    def test_both_tools_return_valid_output(self):
        """Both tools should work and return non-empty strings"""
        flight_result = search_flights_tool("Paris", "Rome", "2026-10-01")
        weather_result = get_weather_tool("Rome")
        
        assert len(flight_result) > 0
        assert len(weather_result) > 0
    
    def test_tools_handle_same_city(self):
        """Tools should handle the same city consistently"""
        city = "Amsterdam"
        flight_result = search_flights_tool("London", city, "2026-11-15")
        weather_result = get_weather_tool(city)
        
        assert city in flight_result
        assert city in weather_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
