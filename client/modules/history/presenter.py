from PySide6.QtWidgets import QMessageBox

class HistoryPresenter:
    def __init__(self, view, model, api_service, event_bus):
        self.view = view
        self.model = model
        self.api = api_service
        self.bus = event_bus

        self.view.back_requested.connect(self.go_back)
        self.view.delete_requested.connect(self.handle_delete)
        self.view.trip_selected.connect(self.handle_select)

    def load_data(self, username):
        self.model.username = username
        self.api.get_history_summary(username, self.on_load_success, self.on_error)

    def on_load_success(self, response):
        trips = response.get("trips", [])
        self.model.trips = trips
        self.view.render_list(trips)

    def handle_delete(self, trip_id):
        confirm = QMessageBox.question(self.view, "Delete", "Are you sure?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.api.delete_trip(trip_id, 
                success_cb=lambda r: self.load_data(self.model.username), 
                error_cb=self.on_error
            )

    def handle_select(self, trip_id):
        # Fetch full details then navigate
        self.api.get_full_trip(trip_id, self.on_trip_details_loaded, self.on_error)

    def on_trip_details_loaded(self, response):
        if "trip" in response:
            self.bus.publish("NAVIGATE", {
                "index": 3, 
                "username": self.model.username,
                "trip_data": response["trip"],
                "mode": "history"
            })

    def go_back(self):
        self.bus.publish("NAVIGATE", {"index": 1, "username": self.model.username})

    def on_error(self, msg):
        print(f"Error: {msg}")