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

    def set_user(self, username):
        """Called by the Shell/Main to update the dashboard before showing it"""
        self.model.username = username
        self.view.set_username_display(username)

    def on_logout(self):
        # Index 0 = Login Screen
        self.bus.publish("NAVIGATE", {"index": 0})

    def on_plan_trip(self):
        # Index 2 = Trip Form Screen
        self.bus.publish("NAVIGATE", {"index": 2, "username": self.model.username})

    def on_history(self):
        # Index 4 = History Screen
        self.bus.publish("NAVIGATE", {"index": 4, "username": self.model.username})

    def on_profile(self):
        # Index 5 = Profile Screen
        self.bus.publish("NAVIGATE", {"index": 5, "username": self.model.username})