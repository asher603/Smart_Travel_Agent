from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QMessageBox, QStackedWidget, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QFont

class LoginScreen(QWidget):
    def __init__(self, switch_callback, api_service):
        super().__init__()
        self.switch_callback = switch_callback
        self.api_service = api_service
        self.init_ui()

    def init_ui(self):
        # לייאוט ראשי - מיישר למרכז
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # --- הכרטיס המרכזי (Login Card) ---
        card = QFrame()
        card.setObjectName("Card")
        card.setFixedWidth(420) # כרטיס רחב ונוח
        
        # אפקט צללית יוקרתי (Drop Shadow)
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 10)
        card.setGraphicsEffect(shadow)

        # עיצוב פנימי של הכרטיס
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(40, 50, 40, 50)

        # --- לוגו ושם המערכת ---
        # אייקון המערכת (טקסטואלי)
        logo_icon = QLabel("✈️")
        logo_icon.setAlignment(Qt.AlignCenter)
        logo_icon.setStyleSheet("font-size: 48px; margin-bottom: 10px;")
        card_layout.addWidget(logo_icon)

        # שם המערכת - גדול ומקצועי
        sys_name = QLabel("Smart Travel Agent")
        sys_name.setAlignment(Qt.AlignCenter)
        sys_name.setStyleSheet("""
            font-family: 'Segoe UI'; 
            font-size: 26px; 
            font-weight: 900; 
            color: #1565c0;
            letter-spacing: 1px;
        """)
        card_layout.addWidget(sys_name)

        # סלוגן קטן
        slogan = QLabel("Your AI-Powered Journey Begins Here")
        slogan.setAlignment(Qt.AlignCenter)
        slogan.setStyleSheet("font-size: 14px; color: #78909c; margin-bottom: 20px;")
        card_layout.addWidget(slogan)

        # --- כפתורי טאבים (Login / Sign Up) ---
        tabs_layout = QHBoxLayout()
        tabs_layout.setSpacing(0)
        
        self.btn_tab_login = QPushButton("Login")
        self.btn_tab_login.setCursor(Qt.PointingHandCursor)
        self.btn_tab_login.setFixedHeight(40)
        self.btn_tab_login.clicked.connect(self.show_login)
        
        self.btn_tab_register = QPushButton("Sign Up")
        self.btn_tab_register.setCursor(Qt.PointingHandCursor)
        self.btn_tab_register.setFixedHeight(40)
        self.btn_tab_register.clicked.connect(self.show_register)

        tabs_layout.addWidget(self.btn_tab_login)
        tabs_layout.addWidget(self.btn_tab_register)
        card_layout.addLayout(tabs_layout)
        
        # קו הפרדה דק מתחת לטאבים
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #e0e0e0; margin-bottom: 15px;")
        card_layout.addWidget(line)

        # --- אזור הטפסים המתחלפים ---
        self.forms_stack = QStackedWidget()
        
        # 1. טופס התחברות
        self.login_widget = QWidget()
        l_layout = QVBoxLayout(self.login_widget)
        l_layout.setSpacing(15)
        l_layout.setContentsMargins(0,0,0,0)
        
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username")
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.Password)
        
        self.login_btn = QPushButton("Login to Account")
        self.login_btn.setObjectName("PrimaryBtn") # משתמש בגרדיאנט מ-styles.py
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.clicked.connect(self.handle_login)

        l_layout.addWidget(self.user_input)
        l_layout.addWidget(self.pass_input)
        l_layout.addSpacing(10)
        l_layout.addWidget(self.login_btn)
        
        # 2. טופס הרשמה
        self.register_widget = QWidget()
        r_layout = QVBoxLayout(self.register_widget)
        r_layout.setSpacing(15)
        r_layout.setContentsMargins(0,0,0,0)

        self.reg_user = QLineEdit()
        self.reg_user.setPlaceholderText("Choose a Username")
        self.reg_pass = QLineEdit()
        self.reg_pass.setPlaceholderText("Create a Password")
        self.reg_pass.setEchoMode(QLineEdit.Password)

        self.reg_btn = QPushButton("Create New Account")
        self.reg_btn.setObjectName("PrimaryBtn")
        # שינוי צבע הכפתור לירוק-כחול עבור הרשמה
        self.reg_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00b09b, stop:1 #96c93d);
                border: none; color: white; border-radius: 10px; padding: 12px; font-weight: bold; font-size: 15px;
            }
            QPushButton:hover { margin-top: -2px; }
        """)
        self.reg_btn.setCursor(Qt.PointingHandCursor)
        self.reg_btn.clicked.connect(self.handle_register)

        r_layout.addWidget(self.reg_user)
        r_layout.addWidget(self.reg_pass)
        r_layout.addSpacing(10)
        r_layout.addWidget(self.reg_btn)

        # הוספה למחסנית
        self.forms_stack.addWidget(self.login_widget)
        self.forms_stack.addWidget(self.register_widget)
        
        card_layout.addWidget(self.forms_stack)
        
        # --- קרדיט תחתון ---
        footer = QLabel("Powered by AI & Hugging Face")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #b0bec5; font-size: 11px; margin-top: 20px;")
        card_layout.addWidget(footer)

        main_layout.addWidget(card)
        
        # אתחול המצב ההתחלתי (התחברות)
        self.show_login()

    def show_login(self):
        self.forms_stack.setCurrentIndex(0)
        # עיצוב טאב פעיל
        self.btn_tab_login.setStyleSheet("background: transparent; color: #1565c0; font-weight: bold; border-bottom: 2px solid #1565c0;")
        self.btn_tab_register.setStyleSheet("background: transparent; color: #90a4ae; font-weight: normal; border: none;")

    def show_register(self):
        self.forms_stack.setCurrentIndex(1)
        # עיצוב טאב פעיל
        self.btn_tab_register.setStyleSheet("background: transparent; color: #00b09b; font-weight: bold; border-bottom: 2px solid #00b09b;")
        self.btn_tab_login.setStyleSheet("background: transparent; color: #90a4ae; font-weight: normal; border: none;")

    def handle_login(self):
        username = self.user_input.text()
        password = self.pass_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Missing Data", "Please enter both username and password.")
            return

        self.login_btn.setText("Authenticating... 🔒")
        self.login_btn.setEnabled(False)
        self.api_service.login(username, password, self.on_login_success, self.on_error)

    def handle_register(self):
        username = self.reg_user.text()
        password = self.reg_pass.text()

        if not username or not password:
            QMessageBox.warning(self, "Missing Data", "Please fill in all fields.")
            return

        self.reg_btn.setText("Creating Account... ✨")
        self.reg_btn.setEnabled(False)
        self.api_service.register(username, password, self.on_register_success, self.on_error)

    def on_login_success(self, response):
        self.login_btn.setText("Login to Account")
        self.login_btn.setEnabled(True)
        username = response.get("username", self.user_input.text())
        
        # מעבר למסך הבא (Trip Form - אינדקס 1)
        self.switch_callback(1, {"username": username})

    def on_register_success(self, response):
        self.reg_btn.setText("Create New Account")
        self.reg_btn.setEnabled(True)
        QMessageBox.information(self, "Welcome!", "Account created successfully! Please log in.")
        self.show_login()
        # מילוי אוטומטי של שם המשתמש שיצרנו
        self.user_input.setText(self.reg_user.text())
        self.pass_input.setFocus()

    def on_error(self, message):
        self.login_btn.setText("Login to Account")
        self.login_btn.setEnabled(True)
        self.reg_btn.setText("Create New Account")
        self.reg_btn.setEnabled(True)
        QMessageBox.critical(self, "Login Failed", f"{message}")