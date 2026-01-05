from PySide6.QtCore import QObject

class TripViewerPresenter(QObject):
    def __init__(self, view, model, api_service, event_bus):
        super().__init__()
        self.view = view
        self.model = model
        self.service = api_service
        self.bus = event_bus

        # 1. Inject API into View (Critical for Workers)
        self.view.set_api(self.service)

        # 2. Connect View Signals
        self.view.back_signal.connect(self.go_back)

        # 3. Connect Bus Signals
        self.bus.subscribe("LOAD_TRIP", self.on_trip_loaded)

    def on_trip_loaded(self, data):
        print(f"👀 Viewer Received Trip Data: {data.keys()}")
        
        # Logic to distinguish New vs Existing
        # "itinerary" suggests a raw plan (New)
        # "chat_history" or "_id" suggests a DB record (Existing)
        
        if "chat_history" in data or "id" in data or "_id" in data:
            print("➡️ Loading Existing Trip")
            self.view.load_existing_trip(data)
        else:
            print("✨ Initializing New Trip")
            # We assume current user is Guest if not tracked
            self.view.init_new_trip(data, "user")

    def go_back(self):
        self.bus.publish("NAVIGATE", {"index": 1}) # Back to Dashboard