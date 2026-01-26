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
        
        # --- התיקון: חילוץ ושמירת ה-ID במודל לפני הכל ---
        # מזהה שמגיע מההיסטוריה (id) או מיצירה חדשה (trip_id)
        current_id = data.get("id") or data.get("trip_id") or data.get("_id")
        
        if current_id:
            self.model.trip_id = str(current_id)  # שמירה במודל כדי שהשמירה תעבוד אחר כך!
        
        # לוגיקת הטעינה
        if "id" in data or "_id" in data:
            self.view.load_existing_trip(data)
            # אם יש היסטוריה במידע שהגיע, נעדכן את ה-View ידנית כדי שיהיה מסונכרן
            if "chat_history" in data:
                self.view.chat_history_state = data["chat_history"]
        else:
            self.view.init_new_trip(data, "guest")

    def go_back(self):
        self.bus.publish("NAVIGATE", {"index": 1})

    def save_chat_state(self, chat_history):
        """שולח את ההיסטוריה לשרת לעדכון"""
        # וודא שיש לנו מזהה טיול
        trip_id = self.model.trip_id
        if not trip_id:
            return

        print(f"💾 Syncing chat state for trip {trip_id}...")
        
        # אנחנו משתמשים ב-api_service כדי לשלוח ברקע
        # אם אין לך post_bg, תשתמש ב-start_worker עם Worker ייעודי
        # אבל לפי הקוד שלך ב-Workers, יש לך StateSaverWorker. אז נשתמש בו.
        
        from .workers import StateSaverWorker
        worker = StateSaverWorker(self.service, trip_id, chat_history)
        worker.start()
        # חשוב: אנחנו לא מחברים finished_signal כי זה Fire & Forget
        # אבל צריך לשמור רפרנס כדי שה-GC לא יהרוג אותו, אז:
        self.view.start_worker(worker)