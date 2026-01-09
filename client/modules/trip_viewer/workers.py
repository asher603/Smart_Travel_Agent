import requests
from PySide6.QtCore import QThread, Signal

# --- WORKERS ---

class ImageWorker(QThread):
    finished_signal = Signal(str) 
    def __init__(self, api, destination, interest):
        super().__init__()
        self.api = api; self.destination = destination; self.interest = interest
    def run(self):
        resp = self.api.post("/ai/generate_image", {"destination": self.destination, "interest": self.interest})
        self.finished_signal.emit(resp.get("image_base64") if resp else None)

class ChatWorker(QThread):
    finished_signal = Signal(str)
    def __init__(self, api, question, context):
        super().__init__()
        self.api = api; self.question = question; self.context = context
    def run(self):
        resp = self.api.post("/ai/ask", {"question": self.question, "context": self.context})
        self.finished_signal.emit(resp.get("answer", "No response") if resp else "Error")

class StateSaverWorker(QThread):
    def __init__(self, api, trip_id, history):
        super().__init__()
        self.api = api; self.trip_id = trip_id; self.history = history
    def run(self):
        self.api.post("/trips/update_state", {"trip_id": self.trip_id, "chat_history": self.history})

class WeatherWorker(QThread):
    finished_signal = Signal(dict)
    def __init__(self, api, destination):
        super().__init__()
        self.api = api; self.destination = destination
    def run(self):
        if hasattr(self.api, 'get_weather'):
            result = self.api.get_weather(self.destination)
            self.finished_signal.emit(result)
        else:
            self.finished_signal.emit({"temp": 0, "desc": "N/A", "icon": "?"})

class BudgetWorker(QThread):
    finished_signal = Signal(dict)
    def __init__(self, api, budget):
        super().__init__()
        self.api = api; self.budget = budget
    def run(self):
        resp = self.api.post("/trips/analyze_budget", {"budget": self.budget})
        self.finished_signal.emit(resp.get("breakdown", {}) if resp else {})

class RefineWorker(QThread):
    finished = Signal(dict)

    def __init__(self, api, trip_id, plan, instr):
        super().__init__()
        self.api = api
        self.trip_id = trip_id
        self.plan = plan
        self.instr = instr

    def run(self):
        payload = {
            "trip_id": self.trip_id,
            "current_plan": self.plan,
            "instructions": self.instr
        }
        res = self.api.post("/trips/refine", payload)

        if res is None:
            self.finished.emit({})
        else:
            self.finished.emit(res)

class FlightWorker(QThread):
    finished_signal = Signal(list)
    
    def __init__(self, api, origin, dest, date):
        super().__init__()
        self.api = api
        self.origin = origin
        self.dest = dest
        self.date = date

    def run(self):
        # 1. Fallback & Validation
        search_from = self.origin if self.origin else "Tel Aviv"
        search_to = self.dest if self.dest else "London"
        search_date = self.date if self.date else "2025-06-01"

        # Prevent Origin == Destination error
        if search_from.strip().lower() == search_to.strip().lower():
            print(f"⚠️ FlightWorker: Origin same as Dest ({search_from}). Defaulting to Tel Aviv.")
            search_from = "Tel Aviv"

        print(f"✈️ FlightWorker: Searching {search_from} -> {search_to} on {search_date}")

        payload = {
            "from": search_from,
            "to": search_to,
            "date": search_date
        }

        # 2. Call Server
        try:
            resp = self.api.post("/trips/flights", payload)
            
            if resp and "flights" in resp:
                self.finished_signal.emit(resp["flights"])
            else:
                self.finished_signal.emit([])
                
        except Exception as e:
            print(f"FlightWorker Error: {e}")
            self.finished_signal.emit([])