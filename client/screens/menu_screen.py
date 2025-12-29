from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QFrame)
from PySide6.QtCore import Qt

class MenuScreen(QWidget):
    def __init__(self, switch_callback):
        super().__init__()
        self.switch_callback = switch_callback
        self.username = "Guest"
        self.setup_ui()

    def set_user(self, username):
        self.username = username
        self.welcome_lbl.setText(f"Hello, {username}! 👋\nWhere to next?")

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; }
            QPushButton {
                background-color: white; border: 1px solid #ddd; border-radius: 10px;
                padding: 20px; text-align: left; font-size: 18px; color: #333;
            }
            QPushButton:hover { background-color: #e3f2fd; border: 1px solid #1565c0; }
            QLabel#Title { font-size: 28px; font-weight: bold; color: #1565c0; }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setFixedSize(450, 500)
        card.setStyleSheet("background: white; border-radius: 15px; border: 1px solid #ddd;")
        
        cl = QVBoxLayout(card)
        cl.setContentsMargins(40, 40, 40, 40)
        cl.setSpacing(20)

        self.welcome_lbl = QLabel("Hello! 👋\nWhere to next?")
        self.welcome_lbl.setObjectName("Title")
        self.welcome_lbl.setAlignment(Qt.AlignCenter)
        cl.addWidget(self.welcome_lbl)
        
        cl.addSpacing(20)

        btn_new = QPushButton("✨  Plan a New Trip")
        btn_new.setCursor(Qt.PointingHandCursor)
        # אינדקס 2 = טופס יצירה
        btn_new.clicked.connect(lambda: self.switch_callback(2)) 
        cl.addWidget(btn_new)

        btn_hist = QPushButton("📜  My Trip History")
        btn_hist.setCursor(Qt.PointingHandCursor)
        # אינדקס 4 = היסטוריה
        btn_hist.clicked.connect(lambda: self.switch_callback(4)) 
        cl.addWidget(btn_hist)

        cl.addStretch()
        
        btn_logout = QPushButton("Log Out")
        btn_logout.setStyleSheet("background: transparent; border: none; color: #777; font-size: 14px; padding: 0;")
        btn_logout.setCursor(Qt.PointingHandCursor)
        btn_logout.clicked.connect(lambda: self.switch_callback(0))
        cl.addWidget(btn_logout, alignment=Qt.AlignCenter)

        layout.addWidget(card)