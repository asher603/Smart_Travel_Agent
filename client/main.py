import sys
import os

# תיקון נתיבים
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtGui import QIcon # <--- חשוב!
from client.api_service import APIService
from client.styles import STYLESHEET
from client.screens.login_screen import LoginScreen
from client.screens.dashboard_screen import DashboardScreen
from client.screens.history_screen import HistoryScreen

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Travel Agent 2.0")
        self.resize(1000, 800)
        self.setStyleSheet(STYLESHEET)
        
        # --- כאן מגדירים את הלוגו לשורת הכותרת ---
        logo_path = os.path.join(current_dir, 'assets', 'logo.png')
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))
        # -----------------------------------------

        self.api = APIService()
        self.stack = QStackedWidget()
        
        self.login = LoginScreen(self.switch, self.api)
        self.dash = DashboardScreen(self.switch, self.api)
        self.hist = HistoryScreen(self.switch, self.api)
        
        self.stack.addWidget(self.login)
        self.stack.addWidget(self.dash)
        self.stack.addWidget(self.hist)
        
        self.setCentralWidget(self.stack)

    def switch(self, n, d):
        idx = 0
        if n == "dashboard": 
            self.dash.set_user(d)
            idx = 1
        elif n == "history": 
            self.hist.load_history(d)
            idx = 2
        self.stack.setCurrentIndex(idx)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # --- מגדירים את האייקון גם בשורת המשימות למטה ---
    logo_path = os.path.join(current_dir, 'assets', 'logo.png')
    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))
    # -----------------------------------------------

    window = MainApp()
    window.show()
    sys.exit(app.exec())