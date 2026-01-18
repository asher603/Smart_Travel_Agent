from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QMessageBox

class DataWorker(QThread):
    finished = Signal(dict)
    def __init__(self, model, username):
        super().__init__()
        self.model = model
        self.username = username
    def run(self):
        data = self.model.fetch_user_data(self.username)
        self.finished.emit(data)

class ProfilePresenter(QObject):
    def __init__(self, view, model, event_bus):
        super().__init__()
        self.view = view
        self.model = model
        self.bus = event_bus

        # View connections
        self.view.back_signal.connect(self.on_back)
        self.view.logout_signal.connect(self.on_logout)
        self.view.save_prefs_signal.connect(self.on_save_prefs)
        self.view.save_identity_signal.connect(self.on_save_identity)
        self.view.change_pass_signal.connect(self.on_change_password)
        
        # Event Bus
        self.bus.subscribe("SHOW_PROFILE", self.load_profile)
        # 1. CRITICAL: Listen for login success from AuthPresenter
        self.bus.subscribe("login_success", self.on_user_login)

    def on_user_login(self, data):
        """Captures the username immediately upon login"""
        username = data.get("username")
        if username:
            self.model.user_stats["username"] = username
            print(f"👤 Profile captured login user: {username}")

    def load_profile(self, data):
        # 2. CRITICAL: Use the captured username
        saved_user = self.model.user_stats.get("username")
        # Priority: Event Data > Saved User > Guest
        username = data.get("username") or saved_user or "Guest"
        
        # Update view immediately so "Guest" doesn't flash
        self.view.update_view({"username": username})
        
        self.worker = DataWorker(self.model, username)
        self.worker.finished.connect(self.on_data_ready)
        self.worker.start()

    def on_data_ready(self, full_data):
        self.view.update_view(full_data)

    def on_save_prefs(self, prefs):
        u = self.model.user_stats.get("username")
        self.model.save_profile_data(u, "preferences", prefs)

    def on_save_identity(self, data):
        u = self.model.user_stats.get("username")
        self.model.save_profile_data(u, "identity", data)
        QMessageBox.information(self.view, "Updated", "Profile updated!")

    def on_change_password(self, o, n):
        u = self.model.user_stats.get("username")
        ok, msg = self.model.change_password(u, o, n)
        if ok: QMessageBox.information(self.view, "Success", msg)
        else: QMessageBox.warning(self.view, "Error", msg)

    def on_back(self): self.bus.publish("NAVIGATE", {"index": 1})
    def on_logout(self): self.model.logout(); self.bus.publish("NAVIGATE", {"index": 0})