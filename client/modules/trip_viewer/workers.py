from PySide6.QtCore import QThread, Signal

class ImageWorker(QThread):
    finished_signal = Signal(str) 
    def __init__(self, api, destination, interest):
        super().__init__()
        self.api = api; self.destination = destination; self.interest = interest
    def run(self):
        try:
            response = self.api.post("/generate_image", {"destination": self.destination, "interest": self.interest})
            self.finished_signal.emit(response.get("image_base64") if response else None)
        except: self.finished_signal.emit(None)

class ChatWorker(QThread):
    finished_signal = Signal(str)
    def __init__(self, api, question, context):
        super().__init__()
        self.api = api; self.question = question; self.context = context
    def run(self):
        try:
            response = self.api.post("/ask_question", {"question": self.question, "context": self.context})
            self.finished_signal.emit(response.get("answer", "No response"))
        except: self.finished_signal.emit("Error connecting")

class StateSaverWorker(QThread):
    def __init__(self, api, trip_id, history):
        super().__init__()
        self.api = api; self.trip_id = trip_id; self.history = history
    def run(self):
        self.api.post("/update_trip_state", {"trip_id": self.trip_id, "chat_history": self.history})

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
            self.finished_signal.emit({"error": "API missing get_weather"})

class FlightWorker(QThread):
    finished_signal = Signal(list)
    def __init__(self, api, origin, dest, date):
        super().__init__()
        self.api = api; self.origin = origin; self.dest = dest; self.date = date
    def run(self):
        resp = self.api.post("/get_flights", {"from": self.origin, "to": self.dest, "date": self.date})
        if resp and "flights" in resp:
            self.finished_signal.emit(resp["flights"])
        else:
            self.finished_signal.emit([])

class RefineWorker(QThread):
    finished = Signal(dict)
    def __init__(self, api, plan, instr):
        super().__init__(); self.api = api; self.plan = plan; self.instr = instr
    def run(self):
        self.finished.emit(self.api.post("/refine_trip", {"current_plan": self.plan, "instruction": self.instr}))