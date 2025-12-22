import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap # <--- חדש
from client.components.custom_widgets import Card

class LoginScreen(QWidget):
    def __init__(self, switch_cb, api):
        super().__init__()
        self.switch_cb, self.api = switch_cb, api
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        
        card = Card()
        card.setFixedSize(400, 550)
        l = QVBoxLayout(card)
        l.setSpacing(20)
        l.setContentsMargins(40,40,40,40)

        # --- החלפת האימוג'י בלוגו אמיתי ---
        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)
        
        # בניית הנתיב לתמונה
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(base_dir, 'assets', 'logo.png')
        
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # משנה גודל ל-80x80 ושומר על פרופורציות
            scaled_pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo.setPixmap(scaled_pixmap)
        else:
            logo.setText("✈️") # גיבוי אם התמונה לא נמצאה
            logo.setStyleSheet("font-size: 60px;")
        
        l.addWidget(logo)
        # -----------------------------------
        
        title = QLabel("Smart Travel")
        title.setObjectName("LoginHeader")
        title.setAlignment(Qt.AlignCenter)

        sub = QLabel("Plan your next adventure")
        sub.setObjectName("LoginSub")
        sub.setAlignment(Qt.AlignCenter)

        self.user = QLineEdit()
        self.user.setPlaceholderText("Username")
        
        self.pwd = QLineEdit()
        self.pwd.setPlaceholderText("Password")
        self.pwd.setEchoMode(QLineEdit.Password)
        
        btn_login = QPushButton("Login")
        btn_login.setObjectName("PrimaryBtn")
        btn_login.setCursor(Qt.PointingHandCursor)
        btn_login.clicked.connect(lambda: self.auth("Login"))

        lbl_or = QLabel("— OR —")
        lbl_or.setAlignment(Qt.AlignCenter)
        lbl_or.setStyleSheet("color: #90a4ae; font-weight: bold;")

        btn_reg = QPushButton("Create Account")
        btn_reg.setObjectName("RegisterBtn")
        btn_reg.setCursor(Qt.PointingHandCursor)
        btn_reg.clicked.connect(lambda: self.auth("Register"))

        l.addWidget(title)
        l.addWidget(sub)
        l.addWidget(self.user)
        l.addWidget(self.pwd)
        l.addWidget(btn_login)
        l.addWidget(lbl_or)
        l.addWidget(btn_reg)
        l.addStretch()

        main_layout.addWidget(card)

    def auth(self, mode):
        u = self.user.text()
        if not u: 
            QMessageBox.warning(self, "Error", "Please enter username")
            return
        
        res = self.api.login(u, self.pwd.text())
        if "error" not in res: 
            self.switch_cb("dashboard", u)
        else: 
            QMessageBox.critical(self, "Error", str(res["error"]))