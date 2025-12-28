import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
    QFrame, QMessageBox, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

class LoginScreen(QWidget):
    def __init__(self, switch_callback, api_service):
        super().__init__()
        self.switch = switch_callback
        self.api = api_service
        
        # משתנה מצב: ברירת מחדל היא התחברות
        self.is_login_mode = True 
        
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        # --- כרטיס ראשי ---
        card = QFrame()
        card.setObjectName("Card") # כדי שה-CSS יזהה אותו
        card.setFixedSize(400, 580) # הגדלתי קצת כדי שהכל יכנס יפה
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(40, 30, 40, 40)

        # --- לוגיקה לטעינת הלוגו ---
        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)
        
        # בניית הנתיב לתמונה
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            logo_path = os.path.join(base_dir, 'client', 'assets', 'logo.png')
            
            # בדיקה שנייה לנתיב קצר יותר (תלוי מאיפה מריצים)
            if not os.path.exists(logo_path):
                 base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                 logo_path = os.path.join(base_dir, 'assets', 'logo.png')

            if os.path.exists(logo_path):
                pixmap = QPixmap(logo_path)
                scaled_pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo.setPixmap(scaled_pixmap)
            else:
                logo.setText("✈️") 
                logo.setStyleSheet("font-size: 60px;")
        except Exception:
            logo.setText("✈️")
            logo.setStyleSheet("font-size: 60px;")
            
        card_layout.addWidget(logo)
        # --------------------------------------

        # --- אזור הטאבים (Login / Sign Up) ---
        tabs_layout = QHBoxLayout()
        tabs_layout.setSpacing(0)
        
        self.tab_login = QPushButton("Login")
        self.tab_login.setProperty("class", "TabBtn") 
        self.tab_login.setCursor(Qt.PointingHandCursor)
        self.tab_login.clicked.connect(lambda: self.set_mode(True))
        
        self.tab_signup = QPushButton("Sign Up")
        self.tab_signup.setProperty("class", "TabBtn")
        self.tab_signup.setCursor(Qt.PointingHandCursor)
        self.tab_signup.clicked.connect(lambda: self.set_mode(False))
        
        tabs_layout.addWidget(self.tab_login)
        tabs_layout.addWidget(self.tab_signup)
        
        # --- כותרת משתנה ---
        self.title_label = QLabel("Welcome Back")
        self.title_label.setObjectName("FormTitle")
        self.title_label.setAlignment(Qt.AlignCenter)

        # --- שדות קלט ---
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username")
        
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.Password)

        # --- כפתור פעולה ראשי ---
        self.action_btn = QPushButton("Login")
        self.action_btn.setObjectName("PrimaryBtn")
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.clicked.connect(self.handle_submit)

        # בניית הכרטיס
        card_layout.addSpacing(10)
        card_layout.addLayout(tabs_layout)
        card_layout.addSpacing(10)
        card_layout.addWidget(self.title_label)
        card_layout.addSpacing(5)
        card_layout.addWidget(self.user_input)
        card_layout.addWidget(self.pass_input)
        card_layout.addSpacing(20)
        card_layout.addWidget(self.action_btn)
        card_layout.addStretch()

        main_layout.addWidget(card)
        
        # הפעלה ראשונית
        self.set_mode(True)

    def set_mode(self, is_login):
        """מעבר בין מצב התחברות להרשמה"""
        self.is_login_mode = is_login
        
        # עדכון עיצוב הטאבים (Active State)
        self.tab_login.setProperty("active", str(is_login).lower())
        self.tab_signup.setProperty("active", str(not is_login).lower())
        
        # רענון סטייל (חובה ב-PySide)
        self.tab_login.style().unpolish(self.tab_login)
        self.tab_login.style().polish(self.tab_login)
        self.tab_signup.style().unpolish(self.tab_signup)
        self.tab_signup.style().polish(self.tab_signup)

        # עדכון טקסטים
        if is_login:
            self.title_label.setText("Welcome Back")
            self.action_btn.setText("Login")
            self.user_input.setPlaceholderText("Username")
        else:
            self.title_label.setText("Create Account")
            self.action_btn.setText("Sign Up")
            self.user_input.setPlaceholderText("Choose a Username")

    def handle_submit(self):
        """שליחת הטופס לשרת"""
        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please fill all fields")
            return

        if self.is_login_mode:
            # --- לוגיקה של התחברות ---
            response = self.api.login(username, password)
            if "error" in response:
                QMessageBox.critical(self, "Login Failed", str(response["error"]))
            else:
                # --- התיקון כאן: שינוי dashboard ל-tripForm ---
                self.switch("tripForm", username)
        else:
            # --- לוגיקה של הרשמה ---
            response = self.api.register(username, password)
            if "error" in response:
                QMessageBox.critical(self, "Registration Failed", str(response["error"]))
            else:
                QMessageBox.information(self, "Success", "Account created! Please login.")
                # מעבר אוטומטי לטאב התחברות
                self.set_mode(True)
                self.pass_input.clear()