from PySide6.QtCore import QObject

class TripFormPresenter(QObject):
    def __init__(self, view, model, api_service, event_bus):
        super().__init__()
        self.view = view
        self.model = model
        self.service = api_service
        self.bus = event_bus

        # Connect View Signals
        self.view.generate_requested.connect(self.handle_generate)
        self.view.back_requested.connect(self.go_back)

    def handle_generate(self, data):
        """
        Handles the 'Generate Trip' click.
        'data' contains strings from the View (e.g., '2025-05-01').
        """
        print(f"📝 Presenter received form data: {data}")
        self.view.show_loading(True)

        # 1. Update Model
        self.model.destination = data.get("destination")
        self.model.start_date = data.get("start_date")
        self.model.end_date = data.get("end_date")
        
        # 2. Prepare Payload
        payload = {
            "destination": data.get("destination"),
            "origin": data.get("origin"),
            "budget": data.get("budget"),
            "currency": data.get("currency"),
            "interests": data.get("interests"),
            "start_date": data.get("start_date"),
            "end_date": data.get("end_date")
        }

        # 3. Call API
        try:
            # We use a Thread or async call in a real app, 
            # but for now we call the service directly (blocking is okay for MVP)
            response = self.service.generate_trip(payload)
            
            self.view.show_loading(False)
            
            if response and "trip" in response:
                print("✅ Trip Generated! Navigating to Viewer...")
                # Navigate to Trip Viewer (Index 4)
                self.bus.publish("NAVIGATE", {"index": 4})
                # Pass the Trip Data to the Viewer
                self.bus.publish("LOAD_TRIP", response["trip"])
            else:
                self.view.show_message("Error", "Failed to generate trip plan.")
                
        except Exception as e:
            self.view.show_loading(False)
            print(f"❌ Generation Error: {e}")
            self.view.show_message("Error", f"Connection failed: {str(e)}")

    def go_back(self):
        self.bus.publish("NAVIGATE", {"index": 1})