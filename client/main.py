import sys
import os

# --- תיקון נתיבים קריטי ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from client.screens.login_screen import LoginScreen
from client.screens.menu_screen import MenuScreen
from client.screens.trip_form_screen import TripFormScreen
from client.screens.trip_screen import TripScreen
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
        self.username = "Guest"

        self.container = QStackedWidget()
        self.container.setObjectName("MainContainer")
        self.setCentralWidget(self.container)

        self.init_screens()

    def init_screens(self):
        # 0: Login
        self.login_screen = LoginScreen(self.handle_login, self.api)
        self.container.addWidget(self.login_screen)

        # 1: Menu
        self.menu_screen = MenuScreen(self.switch_screen)
        self.container.addWidget(self.menu_screen)

        # 2: Form
        self.trip_form_screen = TripFormScreen(self.api)
        self.trip_form_screen.trip_generated.connect(self.handle_trip_generated)
        self.container.addWidget(self.trip_form_screen)

        # 3: Trip Results
        self.trip_screen = TripScreen(self.switch_screen, self.api)
        self.container.addWidget(self.trip_screen)

        # 4: History
        self.history_screen = HistoryScreen(self.switch_screen, self.api)
        self.container.addWidget(self.history_screen)

    def handle_login(self, index, data=None):
        # כשמתחברים, שומרים את שם המשתמש ב-MainApp
        if isinstance(data, str):
            self.username = data
        elif isinstance(data, dict) and "username" in data:
            self.username = data["username"]
        
        # מעדכנים את מסך התפריט
        self.menu_screen.set_user(self.username)
        self.switch_screen(1)

    def switch_screen(self, index, data=None, mode=None):
        # --- עדכונים לפני מעבר מסך ---
        if index == 2: # כניסה לטופס
            self.trip_form_screen.username = self.username
            
        if index == 4: # כניסה להיסטוריה
            self.history_screen.load_history(self.username)
            
        if index == 3 and mode == "load" and data: # טעינה מהיסטוריה
            self.trip_screen.load_existing_trip(data)

        self.container.setCurrentIndex(index)

    def handle_trip_generated(self, trip_data):
        self.trip_screen.init_new_trip(trip_data, self.username)
        self.switch_screen(3)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())