import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QMessageBox, QStackedWidget, 
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property, QPoint, Signal, QSize
from PySide6.QtGui import QColor, QFont, QCursor

# --- רכיבים גרפיים ועיצוביים ---

class FloatingParticle(QFrame):
    """חלקיק מרחף (עיגול חצי שקוף)"""
    def __init__(self, parent, x, y, size):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.move(x, y)
        # עיצוב עיגול לבן חצי שקוף
        self.setStyleSheet(f"""
            background-color: rgba(255, 255, 255, {random.randint(10, 30)});
            border-radius: {size // 2}px;
        """)
        
        # אנימציה: עולה למעלה ונעלם לאט
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(random.randint(5000, 10000))
        self.anim.setStartValue(QPoint(x, y))
        self.anim.setEndValue(QPoint(x, y - 100)) # תנועה למעלה
        self.anim.setEasingCurve(QEasingCurve.InOutSine)
        self.anim.setLoopCount(-1) # אינסופי
        self.anim.start()

class ModernInput(QFrame):
    """שדה קלט מעוצב עם אייקון וכפתור עין"""
    returnPressed = Signal() # סיגנל ללחיצת אנטר

    def __init__(self, placeholder="", is_password=False, icon_char=""):
        super().__init__()
        self.setFixedHeight(55)
        self.setStyleSheet(self._style(focused=False))
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(10)
        
        # אייקון
        if icon_char:
            self.icon_lbl = QLabel(icon_char)
            self.icon_lbl.setStyleSheet("border: none; background: transparent; font-size: 18px; color: #94A3B8;")
            layout.addWidget(self.icon_lbl)

        # שדה טקסט
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(placeholder)
        self.input_field.setStyleSheet("""
            QLineEdit { border: none; background: transparent; font-size: 15px; color: #1E293B; font-family: 'Segoe UI'; }
            QLineEdit::placeholder { color: #94A3B8; }
        """)
        self.input_field.returnPressed.connect(self.returnPressed.emit)
        
        # אירועי פוקוס ידניים כדי לשנות את המסגרת
        self.input_field.focusInEvent = self._on_focus
        self.input_field.focusOutEvent = self._on_blur
        
        layout.addWidget(self.input_field)

        # כפתור סיסמה
        if is_password:
            self.input_field.setEchoMode(QLineEdit.Password)
            self.eye_btn = QPushButton("👁️")
            self.eye_btn.setCursor(Qt.PointingHandCursor)
            self.eye_btn.setFixedSize(30, 30)
            self.eye_btn.setStyleSheet("border: none; background: transparent; font-size: 16px; color: #94A3B8;")
            self.eye_btn.clicked.connect(self.toggle_visibility)
            layout.addWidget(self.eye_btn)

    def _style(self, focused):
        color = "#3B82F6" if focused else "#E2E8F0"
        bg = "#FFFFFF" if focused else "#F8FAFC"
        return f"""
            QFrame {{
                background-color: {bg};
                border: 2px solid {color};
                border-radius: 12px;
            }}
        """

    def _on_focus(self, event):
        self.setStyleSheet(self._style(focused=True))
        if hasattr(self, 'icon_lbl'): self.icon_lbl.setStyleSheet("border: none; background: transparent; font-size: 18px; color: #3B82F6;")
        QLineEdit.focusInEvent(self.input_field, event)

    def _on_blur(self, event):
        self.setStyleSheet(self._style(focused=False))
        if hasattr(self, 'icon_lbl'): self.icon_lbl.setStyleSheet("border: none; background: transparent; font-size: 18px; color: #94A3B8;")
        QLineEdit.focusOutEvent(self.input_field, event)

    def toggle_visibility(self):
        if self.input_field.echoMode() == QLineEdit.Password:
            self.input_field.setEchoMode(QLineEdit.Normal)
            self.eye_btn.setText("🙈")
        else:
            self.input_field.setEchoMode(QLineEdit.Password)
            self.eye_btn.setText("👁️")

    def text(self): return self.input_field.text()
    def setText(self, t): self.input_field.setText(t)
    def setFocus(self): self.input_field.setFocus()


class ScaleButton(QPushButton):
    """כפתור עם אפקט כיווץ בלחיצה (Tactile Feel)"""
    def __init__(self, text, bg_start, bg_end):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(50)
        self.default_style = f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {bg_start}, stop:1 {bg_end});
                color: white; border: none; border-radius: 12px;
                font-size: 16px; font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {bg_end}, stop:1 {bg_start});
            }}
        """
        self.setStyleSheet(self.default_style)

    def mousePressEvent(self, e):
        # אפקט כיווץ ע"י הוספת Margin
        self.setStyleSheet(self.default_style + "QPushButton { margin: 2px; }")
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.setStyleSheet(self.default_style + "QPushButton { margin: 0px; }")
        super().mouseReleaseEvent(e)


class TabButton(QPushButton):
    """כפתור בחירה (Login/Signup)"""
    def __init__(self, text):
        super().__init__(text)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(40)
        self.update_style(False)

    def update_style(self, active):
        if active:
            self.setStyleSheet("""
                QPushButton {
                    background-color: white; color: #1E293B; font-weight: bold; font-size: 14px;
                    border-radius: 10px; border: none;
                }
            """)
            # הוספת צל עדין לטאב הפעיל
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10); shadow.setColor(QColor(0,0,0,20)); shadow.setOffset(0,2)
            self.setGraphicsEffect(shadow)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: transparent; color: #64748B; font-weight: 600; font-size: 14px;
                    border: none;
                }
            """)
            self.setGraphicsEffect(None)


class LoginScreen(QWidget):
    def __init__(self, switch_callback, api_service):
        super().__init__()
        self.switch_callback = switch_callback
        self.api_service = api_service
        self.init_ui()

    def init_ui(self):
        # רקע כללי כהה ואלגנטי
        self.setStyleSheet("background: #0F172A; font-family: 'Segoe UI';")
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        # --- הקונטיינר הראשי (Split View) ---
        container = QWidget()
        container.setFixedSize(900, 550) # גודל קבוע ורחב
        container.setStyleSheet("background: transparent;")
        
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        # ==========================================
        # צד שמאל: מיתוג וחלקיקים (Branding)
        # ==========================================
        self.left_panel = QFrame()
        self.left_panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3B82F6, stop:1 #2563EB);
                border-top-left-radius: 20px;
                border-bottom-left-radius: 20px;
            }
        """)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setAlignment(Qt.AlignCenter)
        
        # יצירת חלקיקים (Particles)
        for _ in range(12):
            size = random.randint(10, 40)
            x = random.randint(20, 300)
            y = random.randint(50, 500)
            p = FloatingParticle(self.left_panel, x, y, size)
            p.show() # לוודא שהם מוצגים

        # תוכן צד שמאל
        logo = QLabel("✈️")
        logo.setStyleSheet("font-size: 80px; background: transparent; border: none;")
        logo.setAlignment(Qt.AlignCenter)
        
        brand_title = QLabel("Smart Travel")
        brand_title.setStyleSheet("font-size: 36px; font-weight: bold; color: white; background: transparent; border: none;")
        brand_title.setAlignment(Qt.AlignCenter)
        
        brand_desc = QLabel("Plan your dream trip with AI.\nPersonalized. Fast. Easy.")
        brand_desc.setStyleSheet("font-size: 16px; color: #E2E8F0; background: transparent; border: none;")
        brand_desc.setAlignment(Qt.AlignCenter)
        
        left_layout.addWidget(logo)
        left_layout.addWidget(brand_title)
        left_layout.addWidget(brand_desc)
        left_layout.addSpacing(20)

        # ==========================================
        # צד ימין: טופס (Form)
        # ==========================================
        self.right_panel = QFrame()
        self.right_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top-right-radius: 20px;
                border-bottom-right-radius: 20px;
            }
        """)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(50, 50, 50, 50)
        right_layout.setSpacing(15)

        # כותרת דינמית
        self.lbl_welcome = QLabel("Welcome Back!")
        self.lbl_welcome.setStyleSheet("font-size: 28px; font-weight: bold; color: #1E293B; border: none;")
        
        self.lbl_subtitle = QLabel("Please enter your details")
        self.lbl_subtitle.setStyleSheet("font-size: 14px; color: #64748B; border: none;")

        right_layout.addWidget(self.lbl_welcome)
        right_layout.addWidget(self.lbl_subtitle)
        right_layout.addSpacing(10)

        # טאבים (Login / Sign Up)
        tabs_container = QFrame()
        tabs_container.setStyleSheet("background-color: #F1F5F9; border-radius: 12px;")
        tabs_container.setFixedHeight(48)
        tabs_layout = QHBoxLayout(tabs_container)
        tabs_layout.setContentsMargins(4, 4, 4, 4)
        
        self.tab_login = TabButton("Log In")
        self.tab_register = TabButton("Sign Up")
        
        self.tab_login.clicked.connect(self.switch_to_login)
        self.tab_register.clicked.connect(self.switch_to_register)
        
        tabs_layout.addWidget(self.tab_login)
        tabs_layout.addWidget(self.tab_register)
        right_layout.addWidget(tabs_container)
        right_layout.addSpacing(10)

        # Stack להחלפת טפסים
        self.stack = QStackedWidget()
        
        # --- טופס התחברות ---
        page_login = QWidget()
        pl = QVBoxLayout(page_login); pl.setContentsMargins(0,0,0,0); pl.setSpacing(15)
        
        self.l_user = ModernInput("Username", icon_char="👤")
        self.l_pass = ModernInput("Password", is_password=True, icon_char="🔒")
        # אנטר בסיסמה מפעיל התחברות
        self.l_pass.returnPressed.connect(self.do_login) 
        
        self.btn_login_action = ScaleButton("Log In", "#3B82F6", "#2563EB")
        self.btn_login_action.clicked.connect(self.do_login)
        
        pl.addWidget(QLabel("Username", styleSheet="color: #475569; font-weight: bold; font-size: 12px; border:none;"))
        pl.addWidget(self.l_user)
        pl.addWidget(QLabel("Password", styleSheet="color: #475569; font-weight: bold; font-size: 12px; border:none;"))
        pl.addWidget(self.l_pass)
        
        forgot_btn = QPushButton("Forgot Password?")
        forgot_btn.setCursor(Qt.PointingHandCursor)
        forgot_btn.setStyleSheet("color: #3B82F6; border: none; text-align: right; font-size: 12px;")
        forgot_btn.clicked.connect(lambda: QMessageBox.information(self, "Reset", "Simulated email sent."))
        
        pl.addWidget(forgot_btn)
        pl.addStretch()
        pl.addWidget(self.btn_login_action)

        # --- טופס הרשמה ---
        page_reg = QWidget()
        pr = QVBoxLayout(page_reg); pr.setContentsMargins(0,0,0,0); pr.setSpacing(15)
        
        self.r_user = ModernInput("Choose Username", icon_char="👤")
        self.r_pass = ModernInput("Choose Password", is_password=True, icon_char="🔒")
        self.r_pass.returnPressed.connect(self.do_register)

        self.btn_reg_action = ScaleButton("Create Account", "#10B981", "#059669")
        self.btn_reg_action.clicked.connect(self.do_register)

        pr.addWidget(QLabel("New Username", styleSheet="color: #475569; font-weight: bold; font-size: 12px; border:none;"))
        pr.addWidget(self.r_user)
        pr.addWidget(QLabel("New Password", styleSheet="color: #475569; font-weight: bold; font-size: 12px; border:none;"))
        pr.addWidget(self.r_pass)
        pr.addStretch()
        pr.addWidget(self.btn_reg_action)

        self.stack.addWidget(page_login)
        self.stack.addWidget(page_reg)
        right_layout.addWidget(self.stack)

        # הוספת שני הפאנלים לראשי
        h_layout.addWidget(self.left_panel)
        h_layout.addWidget(self.right_panel)
        
        # צללית לקונטיינר כולו
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 10)
        container.setGraphicsEffect(shadow)

        main_layout.addWidget(container)

        # אתחול
        self.switch_to_login()

    # --- לוגיקה ---

    def switch_to_login(self):
        self.stack.setCurrentIndex(0)
        self.lbl_welcome.setText("Welcome Back!")
        self.lbl_subtitle.setText("Enter your credentials to access your trips.")
        self.tab_login.update_style(True)
        self.tab_register.update_style(False)
        self.tab_login.setChecked(True)
        self.tab_register.setChecked(False)

    def switch_to_register(self):
        self.stack.setCurrentIndex(1)
        self.lbl_welcome.setText("Get Started")
        self.lbl_subtitle.setText("Create a new account to start planning.")
        self.tab_login.update_style(False)
        self.tab_register.update_style(True)
        self.tab_login.setChecked(False)
        self.tab_register.setChecked(True)

    def do_login(self):
        u = self.l_user.text().strip()
        p = self.l_pass.text().strip()
        if not u or not p:
            return QMessageBox.warning(self, "Missing Info", "Please fill all fields.")
        
        self.btn_login_action.setText("Checking...")
        self.btn_login_action.setEnabled(False)
        self.api_service.login(u, p, self.on_login_success, lambda e: self.on_fail(e, self.btn_login_action, "Log In"))

    def do_register(self):
        u = self.r_user.text().strip()
        p = self.r_pass.text().strip()
        if not u or not p:
            return QMessageBox.warning(self, "Missing Info", "Please fill all fields.")
        
        self.btn_reg_action.setText("Creating...")
        self.btn_reg_action.setEnabled(False)
        self.api_service.register(u, p, self.on_reg_success, lambda e: self.on_fail(e, self.btn_reg_action, "Create Account"))

    def on_login_success(self, res):
        self.btn_login_action.setText("Success!")
        username = res.get("username", self.l_user.text())
        self.switch_callback(1, {"username": username})

    def on_reg_success(self, res):
        QMessageBox.information(self, "Success", "Account created! Please log in.")
        self.switch_to_login()
        self.l_user.setText(self.r_user.text())
        self.btn_reg_action.setText("Create Account")
        self.btn_reg_action.setEnabled(True)

    def on_fail(self, err, btn, reset_text):
        QMessageBox.warning(self, "Error", str(err))
        btn.setText(reset_text)
        btn.setEnabled(True)