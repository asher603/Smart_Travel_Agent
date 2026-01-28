from PySide6.QtCore import QObject

class TripViewerPresenter(QObject):
    def __init__(self, view, model, api_service, event_bus):
        super().__init__()
        self.view = view
        self.model = model
        self.service = api_service
        self.bus = event_bus

        # 1. Inject API so Workers function
        self.view.set_api(self.service)

        # 2. Connect Signals
        self.view.state_updated_signal.connect(self.save_chat_state)
        self.view.back_signal.connect(self.go_back)
        self.bus.subscribe("LOAD_TRIP", self.on_trip_loaded)

    def on_trip_loaded(self, data):
        print(f"👀 Viewer Loaded: {data.get('destination')}")
        
        # Extract and store the trip ID in the model first
        # ID may come from history (id) or new creation (trip_id)
        current_id = data.get("id") or data.get("trip_id") or data.get("_id")
        
        if current_id:
            self.model.trip_id = str(current_id)  # Store in model for later saves
        
        # Loading logic
        if "id" in data or "_id" in data:
            self.view.load_existing_trip(data)
            # If history data was provided, update the View manually to keep in sync
            if "chat_history" in data:
                self.view.chat_history_state = data["chat_history"]
        else:
            self.view.init_new_trip(data, "guest")

    def go_back(self):
        self.bus.publish("NAVIGATE", {"index": 1})

    def save_chat_state(self, chat_history):
        """Send chat history to server for update"""
        # Ensure we have a trip ID
        trip_id = self.model.trip_id
        if not trip_id:
            return

        print(f"💾 Syncing chat state for trip {trip_id}...")
        
        # Use api_service to send in background
        # If post_bg is unavailable, use start_worker with a dedicated Worker
        # Based on your code in Workers, you have StateSaverWorker, so we use that
        
        from .workers import StateSaverWorker
        worker = StateSaverWorker(self.service, trip_id, chat_history)
        worker.start()
        # Note: Not connecting finished_signal since this is Fire & Forget
        # But we need to keep a reference so GC doesn't kill it:
        self.view.start_worker(worker)