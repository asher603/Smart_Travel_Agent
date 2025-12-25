import sys
import os

# תיקון נתיבים (כדי שהפייתון ימצא את התיקייה client)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtGui import QIcon
from client.api_service import APIService
from client.styles import STYLESHEET

# ייבוא המסכים
from client.screens.login_screen import LoginScreen
from client.screens.dashboard_screen import DashboardScreen
from client.screens.history_screen import HistoryScreen

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Travel Agent 2.0")
        self.resize(1000, 800)
        self.setStyleSheet(STYLESHEET)
        
        # --- הגדרת אייקון ---
        logo_path = os.path.join(current_dir, 'assets', 'logo.png')
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))
        # --------------------

        # אתחול שירות ה-API
        self.api = APIService()
        
        # ניהול המעבר בין מסכים
        self.stack = QStackedWidget()
        
        # יצירת המסכים - מעבירים להם את פונקציית המעבר ואת ה-API
        self.login = LoginScreen(self.switch_screen, self.api)
        self.dash = DashboardScreen(self.switch_screen, self.api)
        self.hist = HistoryScreen(self.switch_screen, self.api)
        
        self.stack.addWidget(self.login)
        self.stack.addWidget(self.dash)
        self.stack.addWidget(self.hist)
        
        self.setCentralWidget(self.stack)

    def switch_screen(self, screen_name, data=None):
        """פונקציה למעבר בין מסכים"""
        idx = 0
        if screen_name == "dashboard": 
            # אם יש נתונים (שם משתמש), מעדכנים את הדשבורד
            if data:
                self.dash.set_user(data)
            idx = 1
        elif screen_name == "history": 
            # טעינת היסטוריה לפני המעבר
            if data:
                self.hist.load_history(data)
            idx = 2
        elif screen_name == "login":
            idx = 0
            
        self.stack.setCurrentIndex(idx)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # הגדרת אייקון לאפליקציה כולה
    logo_path = os.path.join(current_dir, 'assets', 'logo.png')
    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))

    window = MainApp()
    window.show()
    sys.exit(app.exec())