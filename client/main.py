import sys
import os

# --- תיקון נתיבים קריטי ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from client.screens.login_screen import LoginScreen
from client.screens.trip_form_screen import TripFormScreen
from client.screens.trip_screen import TripScreen # עכשיו זה יעבוד
from client.screens.history_screen import HistoryScreen
from client.api_service import APIService
from client.styles import STYLESHEET

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Travel Agent ✈️")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(STYLESHEET)
        
        self.api = APIService()
        self.username = "Guest" # נשמור את שם המשתמש כאן

        self.container = QStackedWidget()
        self.container.setObjectName("MainContainer")
        self.setCentralWidget(self.container)

        self.init_screens()

    def init_screens(self):
        # מסך 0: התחברות
        self.login_screen = LoginScreen(self.handle_login, self.api)
        self.container.addWidget(self.login_screen)

        # מסך 1: טופס
        self.trip_form_screen = TripFormScreen(self.api)
        self.trip_form_screen.trip_generated.connect(self.handle_trip_generated)
        self.container.addWidget(self.trip_form_screen)

        # מסך 2: תוצאות (התיקון: מעבירים גם את ה-API)
        self.trip_screen = TripScreen(self.switch_screen, self.api)
        self.container.addWidget(self.trip_screen)

        # מסך 3: היסטוריה
        self.history_screen = HistoryScreen(self.switch_screen, self.api)
        self.container.addWidget(self.history_screen)

    def handle_login(self, index, data=None):
        # פונקציה מיוחדת ששומרת את המשתמש אחרי התחברות
        if data and "username" in data:
            self.username = data["username"]
        self.switch_screen(index)

    def switch_screen(self, index, data=None):
        self.container.setCurrentIndex(index)
        if index == 3: # היסטוריה
            self.history_screen.load_history()

    def handle_trip_generated(self, trip_data):
        # כאן אנחנו מפעילים את הפונקציה שתציג את הטיול
        self.trip_screen.display_trip(trip_data, self.username)
        self.switch_screen(2)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())