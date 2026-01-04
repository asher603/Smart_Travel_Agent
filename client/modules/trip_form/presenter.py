class TripFormPresenter:
    def __init__(self, view, model, api_service, event_bus):
        self.view = view
        self.model = model
        self.api = api_service
        self.bus = event_bus

        self.view.generate_requested.connect(self.handle_generate)
        self.view.back_requested.connect(self.go_back)

    def set_user(self, username):
        self.model.username = username

    def go_back(self):
        # Index 1 = Dashboard
        self.bus.publish("NAVIGATE", {"index": 1, "username": self.model.username})

    def handle_generate(self, form_data):
        # 1. Update Model
        self.model.destination = form_data['destination']
        self.model.origin = form_data['origin']
        self.model.start_date = form_data['start_date']
        self.model.end_date = form_data['end_date']
        
        try:
            self.model.budget = int(form_data['budget'])
        except ValueError:
            self.model.budget = 0

        # 2. Validate
        is_valid, err = self.model.is_valid()
        if not is_valid:
            # Note: View should ideally have a show_error method
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self.view, "Error", err) 
            return

        # 3. Call API
        self.view.show_loading(True)
        
        request_payload = {
            "username": self.model.username,
            "destination": self.model.destination,
            "origin": self.model.origin,
            "budget": self.model.budget,
            "currency": form_data['currency'],
            "interest": form_data['interests'],
            "start_date": self.model.start_date.strftime("%Y-%m-%d"),
            "end_date": self.model.end_date.strftime("%Y-%m-%d")
        }

        self.api.generate_trip(request_payload, self.on_success, self.on_error)

    def on_success(self, response_data):
        self.view.show_loading(False)
        # 4. Navigate to Result Screen (Index 3) with Data
        self.bus.publish("NAVIGATE", {
            "index": 3, 
            "username": self.model.username,
            "trip_data": response_data,
            "mode": "new"
        })

    def on_error(self, error_msg):
        self.view.show_loading(False)
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self.view, "Generation Failed", str(error_msg))