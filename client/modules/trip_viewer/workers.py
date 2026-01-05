from PySide6.QtCore import QThread, Signal

class ImageWorker(QThread):
    finished_signal = Signal(str) 
    def __init__(self, api, destination, interest):
        super().__init__()
        self.api = api; self.destination = destination; self.interest = interest
    def run(self):
        # FIX: Endpoint updated to /ai/generate_image
        resp = self.api.post("/ai/generate_image", {"destination": self.destination, "interest": self.interest})
        self.finished_signal.emit(resp.get("image_base64") if resp else None)

class ChatWorker(QThread):
    finished_signal = Signal(str)
    def __init__(self, api, question, context):
        super().__init__()
        self.api = api; self.question = question; self.context = context
    def run(self):
        # FIX: Endpoint updated to /ai/ask
        resp = self.api.post("/ai/ask", {"question": self.question, "context": self.context})
        self.finished_signal.emit(resp.get("answer", "No response") if resp else "Error")

class StateSaverWorker(QThread):
    def __init__(self, api, trip_id, history):
        super().__init__()
        self.api = api; self.trip_id = trip_id; self.history = history
    def run(self):
        # FIX: Endpoint updated to /trips/update_state
        self.api.post("/trips/update_state", {"trip_id": self.trip_id, "chat_history": self.history})

class WeatherWorker(QThread):
    finished_signal = Signal(dict)
    def __init__(self, api, destination):
        super().__init__()
        self.api = api; self.destination = destination
    def run(self):
        # This uses the method we added to APIService
        if hasattr(self.api, 'get_weather'):
            result = self.api.get_weather(self.destination)
            self.finished_signal.emit(result)
        else:
            self.finished_signal.emit({"temp": 0, "desc": "N/A", "icon": "?"})

class FlightWorker(QThread):
    finished_signal = Signal(list)
    def __init__(self, api, origin, dest, date):
        super().__init__()
        self.api = api; self.origin = origin; self.dest = dest; self.date = date
    def run(self):
        # FIX: Endpoint updated to /trips/flights
        resp = self.api.post("/trips/flights", {"from": self.origin, "to": self.dest, "date": self.date})
        self.finished_signal.emit(resp.get("flights", []) if resp else [])

class BudgetWorker(QThread):
    finished_signal = Signal(dict)
    def __init__(self, api, budget):
        super().__init__()
        self.api = api; self.budget = budget
    def run(self):
        # FIX: Endpoint updated to /trips/analyze_budget
        resp = self.api.post("/trips/analyze_budget", {"budget": self.budget})
        self.finished_signal.emit(resp.get("breakdown", {}) if resp else {})
        
class RefineWorker(QThread):
    finished = Signal(dict)
    def __init__(self, api, plan, instr):
        super().__init__(); self.api = api; self.plan = plan; self.instr = instr
    def run(self):
        # FIX: Endpoint updated to /trips/refine
        self.finished.emit(self.api.post("/trips/refine", {"current_plan": self.plan, "instruction": self.instr}))