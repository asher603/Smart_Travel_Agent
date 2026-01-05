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
        self.view.back_signal.connect(self.go_back)
        self.bus.subscribe("LOAD_TRIP", self.on_trip_loaded)

    def on_trip_loaded(self, data):
        print(f"👀 Viewer Loaded: {data.get('destination')}")
        
        # If it has an ID, it's saved. If not, it's fresh.
        if "id" in data or "_id" in data:
            self.view.load_existing_trip(data)
        else:
            # Pass 'guest' or fetch real username if available
            self.view.init_new_trip(data, "guest")

    def go_back(self):
        self.bus.publish("NAVIGATE", {"index": 1})