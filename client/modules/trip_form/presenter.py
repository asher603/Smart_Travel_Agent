from PySide6.QtCore import QObject, QThread, Signal
from core.security import validate_and_protect

# Worker to run API call in background
class GenerateTripWorker(QThread):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, api_service, payload):
        super().__init__()
        self.service = api_service
        self.payload = payload

    def run(self):
        try:
            result = self.service.generate_trip(self.payload)
            
            if result and "trip" in result:
                self.finished.emit(result["trip"])
            elif result and "detail" in result:
                # Handle FastAPI Error Messages
                self.error.emit(str(result["detail"]))
            else:
                self.error.emit("Unknown API Error")
        except Exception as e:
            self.error.emit(str(e))

class TripFormPresenter(QObject):
    def __init__(self, view, model, api_service, event_bus):
        super().__init__()
        self.view = view
        self.model = model
        self.service = api_service
        self.bus = event_bus

        self.view.generate_requested.connect(self.handle_generate)
        self.view.back_requested.connect(self.go_back)
        self.worker = None

        # --- Subscribe to login event ---
        self.bus.subscribe("login_success", self.on_login)

    def on_login(self, data):
        """Updates the model with the logged-in username AND email."""
        # Extract user data from login event
        username = data.get("username")
        email = data.get("email")
        
        if username:
            print(f"📝 TripForm received user: {username}")
            self.model.username = username
            
        if email:
            print(f"📧 TripForm received email: {email}")
            self.model.email = email

    def handle_generate(self, data):
        # 🛡️ SECURITY CHECK - Prompt Injection Protection
        if not validate_and_protect(
            destination=data.get("destination"),
            origin=data.get("origin"),
            interests=data.get("interests")
        ):
            return
        
        # 1. Lock UI
        self.view.show_loading(True)

        # 2. Prepare Data
        payload = {
            "destination": data.get("destination"),
            "origin": data.get("origin"),
            "budget": data.get("budget"),
            "currency": data.get("currency"),
            "interests": data.get("interests"),
            "start_date": data.get("start_date"),
            "end_date": data.get("end_date"),
            "username": self.model.username or "guest",
            "email": self.model.email or "user@example.com",
            "model": data.get("model", "gemini"),
            "gender": data.get("gender", "male")
        }

        # 3. Start Background Worker
        self.worker = GenerateTripWorker(self.service, payload)
        self.worker.finished.connect(self.on_success)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_success(self, trip_data):
        self.view.show_loading(False)
        print("✅ Trip Generated! Navigating...")
        self.bus.publish("TRIP_CREATED", None)
        self.bus.publish("NAVIGATE", {"index": 4})
        self.bus.publish("LOAD_TRIP", trip_data)

    def on_error(self, error_msg):
        self.view.show_loading(False)
        print(f"❌ Generation Error: {error_msg}")
        self.view.show_message("Error", f"Generation Failed:\n{error_msg}")

    def go_back(self):
        self.bus.publish("NAVIGATE", {"index": 1})