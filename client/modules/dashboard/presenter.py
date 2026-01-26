class DashboardPresenter:
    def __init__(self, view, model, event_bus):
        self.view = view
        self.model = model
        self.bus = event_bus

        # Subscribe to View actions
        self.view.logout_requested.connect(self.on_logout)
        self.view.plan_trip_requested.connect(self.on_plan_trip)
        self.view.history_requested.connect(self.on_history)
        self.view.profile_requested.connect(self.on_profile)

        # --- תיקון: הקשבה לאירוע התחברות ---
        # ברגע שיש לוגין מוצלח, המודל שלנו יקבל את שם המשתמש האמיתי
        self.bus.subscribe("login_success", self.on_user_login)

    def on_user_login(self, data):
        """פונקציה שמופעלת אוטומטית כשיש אירוע login_success"""
        username = data.get("username")
        if username:
            # עדכון המודל והתצוגה עם השם האמיתי
            self.set_user(username)

    def set_user(self, username):
        """Called by the Shell/Main to update the dashboard before showing it"""
        self.model.username = username
        self.view.set_username_display(username)

    def on_logout(self):
        # Index 0 = Login Screen
        self.bus.publish("NAVIGATE", {"index": 0})

    def on_plan_trip(self):
        # Index 3 = Trip Form Screen
        self.bus.publish("NAVIGATE", {"index": 3, "username": self.model.username})

    def on_history(self):
        # Index 2 = History Screen
        self.bus.publish("NAVIGATE", {"index": 2, "username": self.model.username})

    def on_profile(self):
        # Index 5 = Profile Screen
        self.bus.publish("NAVIGATE", {"index": 5, "username": self.model.username})