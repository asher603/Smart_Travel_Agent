import requests
from PySide6.QtCore import QThread, Signal

# --- RESTORED WORKERS (החזרנו את המחלקות החסרות) ---

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
    def __init__(self, api, plan, instr):
        super().__init__(); self.api = api; self.plan = plan; self.instr = instr
    def run(self):
        self.finished.emit(self.api.post("/trips/refine", {"current_plan": self.plan, "instruction": self.instr}))

# --- FIXED FLIGHT WORKER (התיקון לטיסות) ---

class FlightWorker(QThread):
    finished_signal = Signal(list)
    
    # שמרנו על המבנה המקורי שה-View מצפה לו
    def __init__(self, api, origin, dest, date):
        super().__init__()
        self.api = api
        self.origin = origin
        self.dest = dest
        self.date = date

    def run(self):
        # 1. מנגנון הגנה (Fallback)
        # אם הנתונים ריקים (None), נשתמש בברירת מחדל כדי שהשרת לא יקרוס (שגיאה 422)
        search_to = self.dest if self.dest else "London"
        search_date = self.date if self.date else "2025-06-01" # תאריך עתידי
        search_from = self.origin if self.origin else "Tel Aviv"

        print(f"✈️ FlightWorker: Searching {search_from} -> {search_to} on {search_date}")

        payload = {
            "from": search_from,
            "to": search_to,
            "date": search_date
        }

        # 2. שליחה לשרת
        try:
            resp = self.api.post("/trips/flights", payload)
            
            # 3. טיפול בתשובה
            if resp and "flights" in resp:
                self.finished_signal.emit(resp["flights"])
            else:
                print(f"FlightWorker: No flights found or error. Resp: {resp}")
                self.finished_signal.emit([])
                
        except Exception as e:
            print(f"FlightWorker Error: {e}")
            self.finished_signal.emit([])