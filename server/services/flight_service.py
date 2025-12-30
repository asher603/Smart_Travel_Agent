import requests
import datetime
import os

class FlightService:
    def __init__(self):
        self.base_url = "https://test.api.amadeus.com"
        self.client_id = os.getenv("AMADEUS_API_KEY")
        self.client_secret = os.getenv("AMADEUS_SECRET")
        self._token = None
        self._token_expiry = datetime.datetime.now()

    def _get_token(self):
        """ Handles OAuth2 authentication to get/refresh access token """
        if self._token and datetime.datetime.now() < self._token_expiry:
            return self._token

        try:
            url = f"{self.base_url}/v1/security/oauth2/token"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            self._token = result['access_token']
            # Set expiry slightly before actual expiry (usually 1799 seconds)
            self._token_expiry = datetime.datetime.now() + datetime.timedelta(seconds=result['expires_in'] - 60)
            return self._token
        except Exception as e:
            print(f"Amadeus Auth Error: {e}")
            return None

    def search_flights(self, origin_city, destination_city, departure_date):
        """
        1. Converts city names to codes.
        2. Searches for flights.
        """
        # Step 1: Convert Names to Codes
        origin_code = self.get_city_code(origin_city)
        dest_code = self.get_city_code(destination_city)

        if not origin_code or not dest_code:
            return {"error": f"Could not find airport codes for {origin_city} or {destination_city}"}

        # Step 2: Search Flights
        token = self._get_token()
        if not token: return {"error": "Authentication failed"}

        try:
            url = f"{self.base_url}/v2/shopping/flight-offers"
            headers = {"Authorization": f"Bearer {token}"}
            params = {
                "originLocationCode": origin_code,
                "destinationLocationCode": dest_code,
                "departureDate": departure_date,
                "adults": 1,
                "max": 5
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                return self._parse_flights(response.json())
            else:
                return {"error": f"API Error: {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}

    def get_city_code(self, city_name):
        """ 
        Converts a city name (e.g., "Paris") to an IATA code (e.g., "PAR").
        """
        token = self._get_token()
        if not token: return None

        try:
            url = f"{self.base_url}/v1/reference-data/locations"
            headers = {"Authorization": f"Bearer {token}"}
            params = {
                "subType": "CITY", 
                "keyword": city_name,
                "page[limit]": 1
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=5)
            data = response.json()
            
            if data and 'data' in data and len(data['data']) > 0:
                return data['data'][0]['iataCode'] # Returns 'PAR' for Paris
                
        except Exception as e:
            print(f"Code Lookup Error: {e}")
            
        return None

    def _parse_flights(self, data):
        simplified_results = []
        if 'data' not in data: return []

        for offer in data['data']:
            try:
                itinerary = offer['itineraries'][0]
                segments = itinerary['segments']
                dep = segments[0]['departure']['at'].split('T')[1][:5]
                arr = segments[-1]['arrival']['at'].split('T')[1][:5]
                carrier = segments[0]['carrierCode']
                price = offer['price']['total']
                currency = offer['price']['currency']

                simplified_results.append({
                    "carrier": carrier,
                    "departure": dep,
                    "arrival": arr,
                    "price": f"{price} {currency}",
                    "stops": len(segments) - 1
                })
            except: continue
                
        return simplified_results

flight_service = FlightService()