from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QMessageBox

class DataWorker(QThread):
    finished = Signal(dict)
    def __init__(self, model):
        super().__init__()
        self.model = model

    def run(self):
        # המודל ייגש לשרת (פעולה איטית) ויחזיר את הנתונים
        data = self.model.fetch_user_data()
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
        self.view.save_identity_signal.connect(self.on_save_identity)
        self.view.change_pass_signal.connect(self.on_change_password)
        
        # Event Bus connections
        self.bus.subscribe("NAVIGATE", self.check_navigation)
        self.bus.subscribe("login_success", self.on_user_login)

    def on_user_login(self, data):
        """שומרים את שם המשתמש מיד כשהוא מתחבר"""
        username = data.get("username")
        if username:
            self.model.set_current_user(username)

    def load_profile(self, data):
        """נקרא כשהמשתמש נכנס למסך הפרופיל"""
        # 1. Optimistic Update: מציגים מיד את מה שיש לנו בזיכרון (שם משתמש)
        # כדי שהמשתמש לא יראה "Guest" עד שהשרת יענה
        initial_data = {
            "username": self.model.current_username or "Guest",
            "email": self.model.user_data.get("email", "")
        }
        self.view.update_view(initial_data)

        # 2. Background Fetch: שולחים בקשה לשרת להביא נתונים עדכניים ומלאים
        if self.model.current_username:
            self.worker = DataWorker(self.model)
            self.worker.finished.connect(self.on_data_ready)
            self.worker.start()

    def on_data_ready(self, full_data):
        """המידע חזר מהשרת - מעדכנים את המסך סופית"""
        self.view.update_view(full_data)

    def on_save_identity(self, data):
        new_email = data.get("email")
        ok, msg = self.model.save_profile_data(new_email)
        
        if ok:
            QMessageBox.information(self.view, "Success", msg)
        else:
            QMessageBox.warning(self.view, "Error", msg)

    def on_change_password(self, old_pass, new_pass):
        ok, msg = self.model.change_password(old_pass, new_pass)
        
        if ok: 
            QMessageBox.information(self.view, "Success", msg)
            self.view.inp_old_pass.clear()
            self.view.inp_new_pass.clear()
        else: 
            QMessageBox.warning(self.view, "Error", msg)

    def on_back(self): 
        self.bus.publish("NAVIGATE", {"index": 1})

    def check_navigation(self, data):
        # בודק אם הניווט הוא למסך הפרופיל (אינדקס 5)
        if data.get("index") == 5:
            # לוקח את שם המשתמש מהאירוע ומעדכן את המודל
            username = data.get("username")
            if username:
                self.model.set_current_user(username)
            
            # מפעיל את טעינת המסך
            self.load_profile(data)
        
    def on_logout(self): 
        self.model.logout()
        self.bus.publish("NAVIGATE", {"index": 0})