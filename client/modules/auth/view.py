import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QMessageBox, QStackedWidget, 
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

# --- IMPORT CUSTOM COMPONENTS ---
# Assuming standard snake_case filenames based on your class names
from components.floating_particle import FloatingParticle
from components.modern_input import ModernInput
from components.scale_button import ScaleButton
from components.tab_button import TabButton

class AuthView(QWidget):
    # Signals for the Presenter to listen to
    login_signal = Signal(str, str)
    register_signal = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Travel Agent")
        self.resize(1000, 650)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background: #0F172A; font-family: 'Segoe UI';")
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        # --- Main Container (Split View) ---
        container = QWidget()
        container.setFixedSize(900, 550)
        container.setStyleSheet("background: transparent;")
        
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        # ==========================================
        # LEFT PANEL: Branding & Particles
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
        
        # Instantiate Particles (Logic from your original code)
        for _ in range(12):
            size = random.randint(10, 40)
            x = random.randint(20, 300)
            y = random.randint(50, 500)
            # Parent is left_panel so they draw on top of the gradient
            p = FloatingParticle(self.left_panel, x, y, size)
            p.show()

        # Branding Text
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
        # RIGHT PANEL: Form Stack
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

        # Dynamic Header
        self.lbl_welcome = QLabel("Welcome Back!")
        self.lbl_welcome.setStyleSheet("font-size: 28px; font-weight: bold; color: #1E293B; border: none;")
        
        self.lbl_subtitle = QLabel("Please enter your details")
        self.lbl_subtitle.setStyleSheet("font-size: 14px; color: #64748B; border: none;")

        right_layout.addWidget(self.lbl_welcome)
        right_layout.addWidget(self.lbl_subtitle)
        right_layout.addSpacing(10)

        # Tabs (Login / Sign Up)
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

        # Form Stack
        self.stack = QStackedWidget()
        
        # --- LOGIN FORM ---
        page_login = QWidget()
        pl = QVBoxLayout(page_login); pl.setContentsMargins(0,0,0,0); pl.setSpacing(15)
        
        self.l_user = ModernInput("Username", icon_char="👤")
        self.l_pass = ModernInput("Password", is_password=True, icon_char="🔒")
        self.l_pass.returnPressed.connect(self.emit_login)
        
        self.btn_login_action = ScaleButton("Log In", "#3B82F6", "#2563EB")
        self.btn_login_action.clicked.connect(self.emit_login)
        
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

        # --- REGISTER FORM ---
        page_reg = QWidget()
        pr = QVBoxLayout(page_reg); pr.setContentsMargins(0,0,0,0); pr.setSpacing(15)
        
        self.r_user = ModernInput("Choose Username", icon_char="👤")
        self.r_pass = ModernInput("Choose Password", is_password=True, icon_char="🔒")
        self.r_pass.returnPressed.connect(self.emit_register)

        self.btn_reg_action = ScaleButton("Create Account", "#10B981", "#059669")
        self.btn_reg_action.clicked.connect(self.emit_register)

        pr.addWidget(QLabel("New Username", styleSheet="color: #475569; font-weight: bold; font-size: 12px; border:none;"))
        pr.addWidget(self.r_user)
        pr.addWidget(QLabel("New Password", styleSheet="color: #475569; font-weight: bold; font-size: 12px; border:none;"))
        pr.addWidget(self.r_pass)
        pr.addStretch()
        pr.addWidget(self.btn_reg_action)

        self.stack.addWidget(page_login)
        self.stack.addWidget(page_reg)
        right_layout.addWidget(self.stack)

        # Add Panels to Main HLayout
        h_layout.addWidget(self.left_panel)
        h_layout.addWidget(self.right_panel)
        
        # Global Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 10)
        container.setGraphicsEffect(shadow)

        main_layout.addWidget(container)

        # Init State
        self.switch_to_login()

    # --- UI LOGIC ---

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

    # --- INTERACTION LOGIC (Emits Signals) ---

    def emit_login(self):
        u = self.l_user.text().strip()
        p = self.l_pass.text().strip()
        if not u or not p:
            self.show_error("Please fill all fields.")
            return
        
        self.btn_login_action.setText("Checking...")
        self.btn_login_action.setEnabled(False)
        self.login_signal.emit(u, p)

    def emit_register(self):
        u = self.r_user.text().strip()
        p = self.r_pass.text().strip()
        if not u or not p:
            self.show_error("Please fill all fields.")
            return

        self.btn_reg_action.setText("Creating...")
        self.btn_reg_action.setEnabled(False)
        self.register_signal.emit(u, p)

    # --- PUBLIC METHODS (For Presenter) ---

    def show_error(self, message):
        QMessageBox.warning(self, "Error", message)
        self._reset_buttons()

    def show_success(self, message):
        QMessageBox.information(self, "Success", message)
        self._reset_buttons()

    def _reset_buttons(self):
        self.btn_login_action.setText("Log In")
        self.btn_login_action.setEnabled(True)
        self.btn_reg_action.setText("Create Account")
        self.btn_reg_action.setEnabled(True)

    def reset_form(self):
        """איפוס כל הטופס - נקרא כשחוזרים למסך אחרי logout"""
        # איפוס שדות הטקסט
        self.l_user.setText("")
        self.l_pass.setText("")
        self.r_user.setText("")
        self.r_pass.setText("")
        
        # איפוס כפתורים
        self._reset_buttons()
        
        # חזרה לטאב login
        self.switch_to_login()