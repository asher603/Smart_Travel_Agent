from PySide6.QtCore import QObject

class HistoryPresenter(QObject):
    def __init__(self, view, model, api_service, event_bus):
        super().__init__()
        self.view = view
        self.model = model
        self.service = api_service
        self.bus = event_bus
        self.current_user = None

        # --- Connect View Signals ---
        self.view.back_signal.connect(self.go_back)
        self.view.trip_clicked_signal.connect(self.load_trip)
        self.view.delete_trip_signal.connect(self.delete_trip)

        # --- Connect Bus Signals ---
        self.bus.subscribe("login_success", self.on_user_login)

    def on_user_login(self, data):
        """Called when user logs in via Auth module"""
        self.current_user = data.get("username")
        self.refresh_list()

    def refresh_list(self):
        if self.current_user:
            print(f"🔄 History: Fetching data for {self.current_user}")
            trips = self.model.get_history(self.service, self.current_user)
            self.view.update_list(trips)

    def load_trip(self, trip_id):
        print(f"📂 History: Loading trip {trip_id}")
        # Fetch full details
        trip_data = self.model.get_trip_details(self.service, trip_id)
        if trip_data:
            # Navigate to Trip Viewer (Index 4) and pass data
            self.bus.publish("NAVIGATE", {"index": 4})
            self.bus.publish("LOAD_TRIP", trip_data)
        else:
            self.view.show_message("Error", "Could not load trip details.")

    def delete_trip(self, trip_id):
        if self.view.confirm_delete():
            success = self.model.delete_trip(self.service, trip_id)
            if success:
                self.refresh_list()
            else:
                self.view.show_message("Error", "Failed to delete trip.")

    def go_back(self):
        # Back to Dashboard (Index 1)
        self.bus.publish("NAVIGATE", {"index": 1})