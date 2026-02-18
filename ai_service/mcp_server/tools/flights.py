"""
MCP Flight Search Tool — Amadeus API Integration
==================================================
Searches for real flights between cities using the Amadeus Flight Offers API.
Uses OAuth2 authentication with automatic token caching.
"""

import os
import datetime
import httpx

# ---------- Configuration ---------- #

_AMADEUS_BASE_URL = "https://test.api.amadeus.com"

# Token cache (module-level singleton)
_token_cache = {"token": None, "expiry": datetime.datetime.min}

# Static IATA code map for common cities (fast + reliable fallback)
STATIC_IATA_CODES = {
    "TEL AVIV": "TLV", "JERUSALEM": "TLV", "LONDON": "LON",
    "PARIS": "PAR", "NEW YORK": "NYC", "AMSTERDAM": "AMS",
    "ROME": "ROM", "BARCELONA": "BCN", "BERLIN": "BER",
    "TOKYO": "TYO", "DUBAI": "DXB", "BANGKOK": "BKK",
    "MADRID": "MAD", "ATHENS": "ATH", "ISTANBUL": "IST",
    "LISBON": "LIS", "PRAGUE": "PRG", "VIENNA": "VIE",
    "ZURICH": "ZRH", "MOSCOW": "MOW", "MUMBAI": "BOM",
}


# ---------- Internal Helpers ---------- #

def _get_amadeus_token() -> str | None:
    """Authenticate with Amadeus OAuth2 and cache the token."""
    if _token_cache["token"] and datetime.datetime.now() < _token_cache["expiry"]:
        return _token_cache["token"]

    client_id = os.getenv("AMADEUS_API_KEY", "")
    client_secret = os.getenv("AMADEUS_SECRET", "")
    if not client_id or not client_secret:
        return None

    try:
        resp = httpx.post(
            f"{_AMADEUS_BASE_URL}/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()
        _token_cache["token"] = result["access_token"]
        _token_cache["expiry"] = datetime.datetime.now() + datetime.timedelta(
            seconds=result.get("expires_in", 1799) - 60
        )
        return _token_cache["token"]
    except Exception as e:
        print(f"Amadeus Auth Error: {e}")
        return None


def _get_iata_code(city: str) -> str | None:
    """Resolve city name to IATA code using static map + Amadeus API fallback."""
    if not city:
        return None
    clean = city.strip().upper()

    # 1. Fast static lookup
    if clean in STATIC_IATA_CODES:
        return STATIC_IATA_CODES[clean]

    # 2. API-based dynamic resolution
    token = _get_amadeus_token()
    if not token:
        return None

    try:
        resp = httpx.get(
            f"{_AMADEUS_BASE_URL}/v1/reference-data/locations",
            params={"subType": "CITY", "keyword": clean, "page[limit]": 1},
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        data = resp.json()
        if data.get("data"):
            return data["data"][0]["iataCode"]
    except Exception:
        pass

    return None


# ---------- Public MCP Tool ---------- #

def search_flights_tool(origin: str, destination: str, date: str) -> str:
    """
    Search for real flights between two cities using the Amadeus API.
    Returns a formatted string with flight options (carrier, times, price, stops).
    """
    # Resolve IATA codes
    origin_code = _get_iata_code(origin)
    dest_code = _get_iata_code(destination)

    if not origin_code or not dest_code:
        return (
            f"Could not resolve airport codes for '{origin}' or '{destination}'. "
            f"Supported cities include: {', '.join(sorted(STATIC_IATA_CODES.keys()))}."
        )

    # Authenticate
    token = _get_amadeus_token()
    if not token:
        return f"Flight search unavailable — Amadeus authentication failed."

    # Search flights
    try:
        resp = httpx.get(
            f"{_AMADEUS_BASE_URL}/v2/shopping/flight-offers",
            params={
                "originLocationCode": origin_code,
                "destinationLocationCode": dest_code,
                "departureDate": date,
                "adults": 1,
                "max": 5,
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )

        if resp.status_code != 200:
            return f"Amadeus API error ({resp.status_code}): {resp.text[:200]}"

        data = resp.json()
        if "data" not in data or not data["data"]:
            return f"No flights found from {origin} ({origin_code}) to {destination} ({dest_code}) on {date}."

        # Parse results into readable format
        lines = [f"Flight options from {origin} ({origin_code}) to {destination} ({dest_code}) on {date}:"]
        for i, offer in enumerate(data["data"], 1):
            try:
                itinerary = offer["itineraries"][0]
                segments = itinerary["segments"]
                dep_time = segments[0]["departure"]["at"].split("T")[1][:5]
                arr_time = segments[-1]["arrival"]["at"].split("T")[1][:5]
                carrier = segments[0]["carrierCode"]
                price = offer["price"]["total"]
                currency = offer["price"]["currency"]
                stops = len(segments) - 1
                stop_text = "Direct" if stops == 0 else f"{stops} stop{'s' if stops > 1 else ''}"
                lines.append(
                    f"{i}. {carrier} — Depart {dep_time}, Arrive {arr_time} — {price} {currency} — {stop_text}"
                )
            except (KeyError, IndexError):
                continue

        return "\n".join(lines) if len(lines) > 1 else f"No parseable flights for {origin} → {destination} on {date}."

    except httpx.TimeoutException:
        return f"Flight search timed out for {origin} → {destination} on {date}."
    except Exception as e:
        return f"Flight search error: {str(e)}"