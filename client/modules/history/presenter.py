from PySide6.QtCore import QObject

class HistoryPresenter(QObject):
    def __init__(self, view, model, api_service, event_bus):
        super().__init__()
        self.view = view
        self.model = model
        self.service = api_service
        self.bus = event_bus
        self.current_user = None

        self.view.back_clicked.connect(self.go_back)
        self.view.trip_selected.connect(self.load_trip)
        self.view.trip_deleted.connect(self.delete_trip)
        
        self.bus.subscribe("login_success", self.on_login)
        # --- שורה חדשה: הרשמה לאירוע יצירת טיול ---
        self.bus.subscribe("TRIP_CREATED", self.on_trip_created)

    def on_login(self, data):
        self.current_user = data.get("username")
        # Trigger refresh immediately on login
        self.refresh()

    # --- פונקציה חדשה: מטפלת ברענון כשנוצר טיול ---
    def on_trip_created(self, _):
        # המקף התחתון (_) מסמן שאנחנו מתעלמים מהמידע שמגיע עם האירוע
        print("✨ New trip created. Refreshing history list...")
        self.refresh()
    # ---------------------------------------------

    def refresh(self):
        print(f"🔄 Refreshing History for {self.current_user}")
        
        # 1. Fetch from Model
        trips = self.model.get_history(self.service, self.current_user)
        
        print(f"📦 API Returned {len(trips)} trips: {trips}")
        
        # 2. Update View (Empty list is fine, it will show 'No trips')
        self.view.update_list(trips)

    def load_trip(self, trip_id):
        print(f"📂 Requesting Trip Details: {trip_id}")
        trip_data = self.model.get_trip_details(self.service, trip_id)
        
        if trip_data:
            print("✅ Trip details loaded. Switching to Viewer.")
            self.bus.publish("NAVIGATE", {"index": 4})
            self.bus.publish("LOAD_TRIP", trip_data)
        else:
            print("❌ Failed to load trip details.")

    def delete_trip(self, trip_id):
        if self.view.confirm_delete():
            if self.model.delete_trip(self.service, trip_id):
                self.refresh()

    def go_back(self):
        self.bus.publish("NAVIGATE", {"index": 1}) # Back to Dashboard