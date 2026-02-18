"""
Tests for MCP Tools — Amadeus Flights & Open-Meteo Weather
==========================================================
Comprehensive unit tests for the MCP server tools.
Uses mocking to isolate tests from real APIs.
"""

import pytest
from unittest.mock import patch, MagicMock
from ai_service.mcp_server.tools.flights import (
    search_flights_tool,
    _get_amadeus_token,
    _get_iata_code,
    _token_cache,
    STATIC_IATA_CODES,
)
from ai_service.mcp_server.tools.weather import get_weather_tool, _WMO_CODES


# ============================== #
#          FLIGHT TESTS           #
# ============================== #

class TestFlightsStaticCodes:
    """Tests for static IATA code resolution"""

    def test_static_code_tel_aviv(self):
        """Tel Aviv should resolve to TLV from static map"""
        assert _get_iata_code("Tel Aviv") == "TLV"

    def test_static_code_case_insensitive(self):
        """City lookup should be case-insensitive"""
        assert _get_iata_code("paris") == "PAR"
        assert _get_iata_code("PARIS") == "PAR"
        assert _get_iata_code("Paris") == "PAR"

    def test_static_code_with_whitespace(self):
        """City lookup should trim whitespace"""
        assert _get_iata_code("  London  ") == "LON"

    def test_static_code_empty_input(self):
        """Empty string should return None"""
        assert _get_iata_code("") is None
        assert _get_iata_code(None) is None

    def test_static_codes_complete(self):
        """All documented cities should be in the static map"""
        expected = ["TEL AVIV", "LONDON", "PARIS", "NEW YORK", "AMSTERDAM",
                    "ROME", "BARCELONA", "BERLIN", "TOKYO", "DUBAI", "BANGKOK"]
        for city in expected:
            assert city in STATIC_IATA_CODES, f"{city} missing from STATIC_IATA_CODES"


class TestFlightsAmadeusAuth:
    """Tests for Amadeus OAuth2 authentication"""

    def setup_method(self):
        """Reset token cache before each test"""
        _token_cache["token"] = None
        _token_cache["expiry"] = __import__("datetime").datetime.min

    @patch.dict("os.environ", {"AMADEUS_API_KEY": "", "AMADEUS_SECRET": ""})
    def test_auth_fails_without_keys(self):
        """Should return None when API keys are missing"""
        assert _get_amadeus_token() is None

    @patch.dict("os.environ", {"AMADEUS_API_KEY": "test_key", "AMADEUS_SECRET": "test_secret"})
    @patch("ai_service.mcp_server.tools.flights.httpx.post")
    def test_auth_success(self, mock_post):
        """Should return token on successful auth"""
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"access_token": "mock_token_123", "expires_in": 1799}
        )
        mock_post.return_value.raise_for_status = MagicMock()
        token = _get_amadeus_token()
        assert token == "mock_token_123"

    @patch.dict("os.environ", {"AMADEUS_API_KEY": "test_key", "AMADEUS_SECRET": "test_secret"})
    @patch("ai_service.mcp_server.tools.flights.httpx.post")
    def test_auth_caches_token(self, mock_post):
        """Token should be cached after first call"""
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"access_token": "cached_token", "expires_in": 1799}
        )
        mock_post.return_value.raise_for_status = MagicMock()
        _get_amadeus_token()
        _get_amadeus_token()  # Second call should use cache
        assert mock_post.call_count == 1  # Only called once

    @patch.dict("os.environ", {"AMADEUS_API_KEY": "key", "AMADEUS_SECRET": "secret"})
    @patch("ai_service.mcp_server.tools.flights.httpx.post", side_effect=Exception("Network error"))
    def test_auth_handles_network_error(self, mock_post):
        """Should return None on network failure"""
        assert _get_amadeus_token() is None


class TestFlightsSearchTool:
    """Tests for the main search_flights_tool function"""

    def setup_method(self):
        _token_cache["token"] = None
        _token_cache["expiry"] = __import__("datetime").datetime.min

    def test_returns_string(self):
        """Tool should always return a string"""
        result = search_flights_tool("Tel Aviv", "UnknownCity123", "2026-03-15")
        assert isinstance(result, str)

    @patch("ai_service.mcp_server.tools.flights._get_amadeus_token", return_value="mock_token")
    @patch("ai_service.mcp_server.tools.flights.httpx.get")
    def test_successful_search(self, mock_get, mock_token):
        """Should parse and format Amadeus flight results"""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "data": [{
                    "itineraries": [{
                        "segments": [{
                            "departure": {"at": "2026-03-15T08:30:00"},
                            "arrival": {"at": "2026-03-15T12:45:00"},
                            "carrierCode": "LY"
                        }]
                    }],
                    "price": {"total": "350.00", "currency": "EUR"}
                }]
            }
        )
        result = search_flights_tool("Tel Aviv", "Paris", "2026-03-15")
        assert "Tel Aviv" in result
        assert "Paris" in result
        assert "LY" in result
        assert "350.00" in result
        assert "EUR" in result
        assert "Direct" in result

    @patch("ai_service.mcp_server.tools.flights._get_amadeus_token", return_value="mock_token")
    @patch("ai_service.mcp_server.tools.flights.httpx.get")
    def test_multi_stop_flight(self, mock_get, mock_token):
        """Should correctly identify multi-stop flights"""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "data": [{
                    "itineraries": [{
                        "segments": [
                            {"departure": {"at": "2026-03-15T08:00:00"}, "arrival": {"at": "2026-03-15T11:00:00"}, "carrierCode": "BA"},
                            {"departure": {"at": "2026-03-15T13:00:00"}, "arrival": {"at": "2026-03-15T16:00:00"}, "carrierCode": "BA"},
                        ]
                    }],
                    "price": {"total": "280.00", "currency": "USD"}
                }]
            }
        )
        result = search_flights_tool("Tel Aviv", "London", "2026-03-15")
        assert "1 stop" in result

    @patch("ai_service.mcp_server.tools.flights._get_amadeus_token", return_value="mock_token")
    @patch("ai_service.mcp_server.tools.flights.httpx.get")
    def test_no_flights_found(self, mock_get, mock_token):
        """Should handle empty results gracefully"""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"data": []}
        )
        result = search_flights_tool("Tel Aviv", "Paris", "2026-03-15")
        assert "No flights found" in result

    @patch("ai_service.mcp_server.tools.flights._get_amadeus_token", return_value="mock_token")
    @patch("ai_service.mcp_server.tools.flights.httpx.get")
    def test_api_error_status(self, mock_get, mock_token):
        """Should handle non-200 API responses"""
        mock_get.return_value = MagicMock(
            status_code=401,
            text="Unauthorized"
        )
        result = search_flights_tool("Tel Aviv", "Paris", "2026-03-15")
        assert "error" in result.lower() or "401" in result

    def test_unknown_city_returns_helpful_message(self):
        """Unknown cities should get a helpful error with available cities"""
        result = search_flights_tool("Atlantis", "Narnia", "2026-03-15")
        assert "Could not resolve" in result or "unavailable" in result.lower()

    @patch("ai_service.mcp_server.tools.flights._get_amadeus_token", return_value="mock_token")
    @patch("ai_service.mcp_server.tools.flights.httpx.get", side_effect=__import__("httpx").TimeoutException("timeout"))
    def test_timeout_handling(self, mock_get, mock_token):
        """Should handle timeout gracefully"""
        result = search_flights_tool("Tel Aviv", "Paris", "2026-03-15")
        assert "timed out" in result.lower()

    @patch("ai_service.mcp_server.tools.flights._get_amadeus_token", return_value="mock_token")
    @patch("ai_service.mcp_server.tools.flights.httpx.get", side_effect=Exception("Connection refused"))
    def test_general_exception_handling(self, mock_get, mock_token):
        """Should handle unexpected errors gracefully"""
        result = search_flights_tool("Tel Aviv", "Paris", "2026-03-15")
        assert "error" in result.lower()

    @patch("ai_service.mcp_server.tools.flights._get_amadeus_token", return_value="mock_token")
    @patch("ai_service.mcp_server.tools.flights.httpx.get")
    def test_multiple_flight_results(self, mock_get, mock_token):
        """Should format multiple flight options with numbering"""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "data": [
                    {
                        "itineraries": [{"segments": [{"departure": {"at": "2026-03-15T06:00:00"}, "arrival": {"at": "2026-03-15T09:00:00"}, "carrierCode": "LY"}]}],
                        "price": {"total": "300.00", "currency": "EUR"}
                    },
                    {
                        "itineraries": [{"segments": [{"departure": {"at": "2026-03-15T14:00:00"}, "arrival": {"at": "2026-03-15T17:30:00"}, "carrierCode": "AF"}]}],
                        "price": {"total": "250.00", "currency": "EUR"}
                    },
                ]
            }
        )
        result = search_flights_tool("Tel Aviv", "Paris", "2026-03-15")
        assert "1." in result
        assert "2." in result
        assert "LY" in result
        assert "AF" in result


class TestFlightsDynamicCodeResolution:
    """Tests for API-based IATA code resolution"""

    def setup_method(self):
        _token_cache["token"] = None
        _token_cache["expiry"] = __import__("datetime").datetime.min

    @patch("ai_service.mcp_server.tools.flights._get_amadeus_token", return_value="mock_token")
    @patch("ai_service.mcp_server.tools.flights.httpx.get")
    def test_dynamic_city_resolution(self, mock_get, mock_token):
        """Should resolve unknown cities via Amadeus API"""
        mock_get.return_value = MagicMock(
            json=lambda: {"data": [{"iataCode": "SIN"}]}
        )
        assert _get_iata_code("Singapore") == "SIN"

    @patch("ai_service.mcp_server.tools.flights._get_amadeus_token", return_value="mock_token")
    @patch("ai_service.mcp_server.tools.flights.httpx.get")
    def test_dynamic_resolution_no_results(self, mock_get, mock_token):
        """Should return None when API has no results"""
        mock_get.return_value = MagicMock(
            json=lambda: {"data": []}
        )
        assert _get_iata_code("FakeCity12345") is None


# ============================== #
#          WEATHER TESTS          #
# ============================== #

class TestWeatherTool:
    """Tests for the weather tool with Open-Meteo integration"""

    @patch("ai_service.mcp_server.tools.weather.httpx.get")
    def test_successful_weather_query(self, mock_get):
        """Should return formatted weather string for valid city"""
        # Mock geocoding response, then weather response
        mock_get.side_effect = [
            MagicMock(json=lambda: {
                "results": [{"latitude": 48.85, "longitude": 2.35, "name": "Paris"}]
            }),
            MagicMock(
                status_code=200,
                json=lambda: {
                    "current_weather": {
                        "temperature": 18.5,
                        "windspeed": 12.3,
                        "weathercode": 0
                    }
                },
                raise_for_status=MagicMock()
            ),
        ]
        result = get_weather_tool("Paris")
        assert "Paris" in result
        assert "18.5°C" in result
        assert "Clear Sky" in result
        assert "☀️" in result
        assert "12.3 km/h" in result

    @patch("ai_service.mcp_server.tools.weather.httpx.get")
    def test_cloudy_weather(self, mock_get):
        """Should correctly map WMO code 2 to Partly Cloudy"""
        mock_get.side_effect = [
            MagicMock(json=lambda: {
                "results": [{"latitude": 51.5, "longitude": -0.12, "name": "London"}]
            }),
            MagicMock(
                status_code=200,
                json=lambda: {
                    "current_weather": {"temperature": 8.0, "windspeed": 20.0, "weathercode": 2}
                },
                raise_for_status=MagicMock()
            ),
        ]
        result = get_weather_tool("London")
        assert "Partly Cloudy" in result
        assert "⛅" in result

    @patch("ai_service.mcp_server.tools.weather.httpx.get")
    def test_rainy_weather(self, mock_get):
        """Should correctly map WMO code 63 to Moderate Rain"""
        mock_get.side_effect = [
            MagicMock(json=lambda: {
                "results": [{"latitude": 35.68, "longitude": 139.69, "name": "Tokyo"}]
            }),
            MagicMock(
                status_code=200,
                json=lambda: {
                    "current_weather": {"temperature": 22.0, "windspeed": 5.0, "weathercode": 63}
                },
                raise_for_status=MagicMock()
            ),
        ]
        result = get_weather_tool("Tokyo")
        assert "Moderate Rain" in result
        assert "🌧️" in result

    @patch("ai_service.mcp_server.tools.weather.httpx.get")
    def test_unknown_city(self, mock_get):
        """Should handle cities not found by geocoding API"""
        mock_get.return_value = MagicMock(json=lambda: {"results": None})
        result = get_weather_tool("FakeCity12345")
        assert "Could not find" in result

    @patch("ai_service.mcp_server.tools.weather.httpx.get")
    def test_empty_geocoding_results(self, mock_get):
        """Should handle empty geocoding results list"""
        mock_get.return_value = MagicMock(json=lambda: {"results": []})
        result = get_weather_tool("Atlantis")
        assert "Could not find" in result

    @patch("ai_service.mcp_server.tools.weather.httpx.get", side_effect=__import__("httpx").TimeoutException("timeout"))
    def test_timeout_handling(self, mock_get):
        """Should handle timeout gracefully"""
        result = get_weather_tool("Paris")
        assert "timed out" in result.lower()

    @patch("ai_service.mcp_server.tools.weather.httpx.get", side_effect=Exception("Network error"))
    def test_general_exception_handling(self, mock_get):
        """Should handle unexpected errors gracefully"""
        result = get_weather_tool("Paris")
        assert "error" in result.lower()

    def test_returns_string(self):
        """Tool should always return a string type"""
        with patch("ai_service.mcp_server.tools.weather.httpx.get") as mock_get:
            mock_get.return_value = MagicMock(json=lambda: {"results": []})
            result = get_weather_tool("Test")
            assert isinstance(result, str)

    @patch("ai_service.mcp_server.tools.weather.httpx.get")
    def test_snow_weather(self, mock_get):
        """Should correctly map WMO code 73 to Moderate Snow"""
        mock_get.side_effect = [
            MagicMock(json=lambda: {
                "results": [{"latitude": 60.17, "longitude": 24.94, "name": "Helsinki"}]
            }),
            MagicMock(
                status_code=200,
                json=lambda: {
                    "current_weather": {"temperature": -5.0, "windspeed": 15.0, "weathercode": 73}
                },
                raise_for_status=MagicMock()
            ),
        ]
        result = get_weather_tool("Helsinki")
        assert "Moderate Snow" in result
        assert "❄️" in result
        assert "-5.0°C" in result

    @patch("ai_service.mcp_server.tools.weather.httpx.get")
    def test_thunderstorm_weather(self, mock_get):
        """Should correctly map WMO code 95 to Thunderstorm"""
        mock_get.side_effect = [
            MagicMock(json=lambda: {
                "results": [{"latitude": 13.75, "longitude": 100.52, "name": "Bangkok"}]
            }),
            MagicMock(
                status_code=200,
                json=lambda: {
                    "current_weather": {"temperature": 32.0, "windspeed": 25.0, "weathercode": 95}
                },
                raise_for_status=MagicMock()
            ),
        ]
        result = get_weather_tool("Bangkok")
        assert "Thunderstorm" in result
        assert "⛈️" in result


class TestWMOCodes:
    """Tests for the WMO weather code mapping"""

    def test_clear_sky_code(self):
        """WMO code 0 should be Clear Sky"""
        assert _WMO_CODES[0] == ("Clear Sky", "☀️")

    def test_all_codes_have_two_elements(self):
        """Each WMO mapping should have (description, emoji) tuple"""
        for code, value in _WMO_CODES.items():
            assert isinstance(value, tuple), f"Code {code} is not a tuple"
            assert len(value) == 2, f"Code {code} doesn't have 2 elements"
            assert isinstance(value[0], str), f"Code {code} description is not a string"
            assert isinstance(value[1], str), f"Code {code} emoji is not a string"

    def test_key_weather_codes_present(self):
        """Critical WMO codes should be mapped"""
        critical_codes = [0, 1, 2, 3, 61, 63, 65, 71, 73, 75, 95]
        for code in critical_codes:
            assert code in _WMO_CODES, f"WMO code {code} is missing"


# ============================== #
#       INTEGRATION TESTS         #
# ============================== #

class TestMCPToolsIntegration:
    """Integration tests for MCP tools working together"""

    def setup_method(self):
        _token_cache["token"] = None
        _token_cache["expiry"] = __import__("datetime").datetime.min

    @patch("ai_service.mcp_server.tools.flights._get_amadeus_token", return_value="mock_token")
    @patch("httpx.get")
    def test_both_tools_return_valid_output(self, mock_get, mock_token):
        """Both tools should work and return non-empty strings"""
        def route_by_url(url, **kwargs):
            if "flight-offers" in url:
                return MagicMock(
                    status_code=200,
                    json=lambda: {
                        "data": [{
                            "itineraries": [{"segments": [{"departure": {"at": "2026-10-01T10:00:00"}, "arrival": {"at": "2026-10-01T12:00:00"}, "carrierCode": "AZ"}]}],
                            "price": {"total": "200.00", "currency": "EUR"}
                        }]
                    }
                )
            elif "geocoding" in url:
                return MagicMock(json=lambda: {"results": [{"latitude": 41.9, "longitude": 12.5, "name": "Rome"}]})
            elif "forecast" in url:
                resp = MagicMock(status_code=200, json=lambda: {"current_weather": {"temperature": 25, "windspeed": 10, "weathercode": 0}})
                resp.raise_for_status = MagicMock()
                return resp
            return MagicMock()

        mock_get.side_effect = route_by_url

        flight_result = search_flights_tool("Paris", "Rome", "2026-10-01")
        weather_result = get_weather_tool("Rome")

        assert len(flight_result) > 0
        assert len(weather_result) > 0
        assert "AZ" in flight_result
        assert "Rome" in weather_result

    @patch("ai_service.mcp_server.tools.weather.httpx.get", side_effect=Exception("Weather API down"))
    def test_weather_failure_isolated_from_flights(self, mock_weather):
        """Weather failure should not affect flight tool"""
        weather_result = get_weather_tool("Rome")
        assert "error" in weather_result.lower()
        # Flights should still work independently (will fail on auth, but won't crash)
        flight_result = search_flights_tool("Tel Aviv", "Rome", "2026-10-01")
        assert isinstance(flight_result, str)

    @patch("ai_service.mcp_server.tools.weather.httpx.get")
    def test_tools_handle_same_city(self, mock_get):
        """Tools should handle the same city consistently"""
        mock_get.side_effect = [
            MagicMock(json=lambda: {"results": [{"latitude": 52.37, "longitude": 4.9, "name": "Amsterdam"}]}),
            MagicMock(status_code=200, json=lambda: {"current_weather": {"temperature": 12, "windspeed": 18, "weathercode": 2}}, raise_for_status=MagicMock()),
        ]
        weather_result = get_weather_tool("Amsterdam")
        assert "Amsterdam" in weather_result

    def test_flight_tool_with_hebrew_cities_static(self):
        """Hebrew city names should be handled (via static codes if mapped)"""
        # Not in STATIC_IATA_CODES, so will try API → fail → return helpful message
        result = search_flights_tool("תל אביב", "פריז", "2026-08-15")
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("ai_service.mcp_server.tools.weather.httpx.get")
    def test_weather_with_resolved_name(self, mock_get):
        """Should use the resolved city name from geocoding"""
        mock_get.side_effect = [
            MagicMock(json=lambda: {"results": [{"latitude": 48.85, "longitude": 2.35, "name": "Paris"}]}),
            MagicMock(status_code=200, json=lambda: {"current_weather": {"temperature": 15, "windspeed": 8, "weathercode": 1}}, raise_for_status=MagicMock()),
        ]
        result = get_weather_tool("paris")
        assert "Paris" in result  # Should use resolved "Paris" not input "paris"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
