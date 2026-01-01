from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QStackedWidget, QComboBox, QGraphicsDropShadowEffect, QLineEdit
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor, QFont
from client.components.custom_widgets import ModernSwitch

# --- רכיבים מותאמים ל-Dark Mode (מוגדרים מקומית לעיצוב מושלם) ---

class DarkInput(QFrame):
    """שדה קלט מותאם לרקע כהה"""
    returnPressed = Signal()

    def __init__(self, placeholder="", is_password=False, icon_char=""):
        super().__init__()
        self.setFixedHeight(52)
        self.setStyleSheet(self._style(focused=False))
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(12)
        
        if icon_char:
            self.icon_lbl = QLabel(icon_char)
            self.icon_lbl.setStyleSheet("border: none; background: transparent; font-size: 18px; color: #64748B;")
            layout.addWidget(self.icon_lbl)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(placeholder)
        self.input_field.setStyleSheet("""
            QLineEdit { 
                border: none; background: transparent; 
                font-size: 15px; color: #F1F5F9; font-family: 'Segoe UI'; font-weight: 500;
            }
            QLineEdit::placeholder { color: #475569; }
        """)
        
        self.input_field.focusInEvent = self._on_focus
        self.input_field.focusOutEvent = self._on_blur
        
        layout.addWidget(self.input_field)

        if is_password:
            self.input_field.setEchoMode(QLineEdit.Password)
            self.eye_btn = QPushButton("👁️")
            self.eye_btn.setCursor(Qt.PointingHandCursor)
            self.eye_btn.setFixedSize(30, 30)
            self.eye_btn.setStyleSheet("border: none; background: transparent; font-size: 16px; color: #64748B;")
            self.eye_btn.clicked.connect(self.toggle_visibility)
            layout.addWidget(self.eye_btn)

    def _style(self, focused):
        # עיצוב כהה: רקע שחור חצי שקוף, גבול אפור כהה או כחול בפוקוס
        border = "#3B82F6" if focused else "#334155"
        bg = "rgba(15, 23, 42, 0.6)" if focused else "rgba(30, 41, 59, 0.4)"
        return f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 12px;
            }}
        """

    def _on_focus(self, event):
        self.setStyleSheet(self._style(focused=True))
        if hasattr(self, 'icon_lbl'): 
            self.icon_lbl.setStyleSheet("border: none; background: transparent; font-size: 18px; color: #3B82F6;")
        QLineEdit.focusInEvent(self.input_field, event)

    def _on_blur(self, event):
        self.setStyleSheet(self._style(focused=False))
        if hasattr(self, 'icon_lbl'): 
            self.icon_lbl.setStyleSheet("border: none; background: transparent; font-size: 18px; color: #64748B;")
        QLineEdit.focusOutEvent(self.input_field, event)

    def toggle_visibility(self):
        if self.input_field.echoMode() == QLineEdit.Password:
            self.input_field.setEchoMode(QLineEdit.Normal)
            self.eye_btn.setText("🙈")
        else:
            self.input_field.setEchoMode(QLineEdit.Password)
            self.eye_btn.setText("👁️")

    def text(self): return self.input_field.text()

class DarkComboBox(QComboBox):
    """קומבו-בוקס כהה"""
    def __init__(self):
        super().__init__()
        self.setFixedHeight(45)
        self.setStyleSheet("""
            QComboBox {
                background-color: rgba(30, 41, 59, 0.4);
                border: 1px solid #334155;
                border-radius: 10px;
                padding-left: 15px;
                font-size: 14px;
                color: #F1F5F9;
            }
            QComboBox:hover { border: 1px solid #3B82F6; }
            QComboBox::drop-down { border: none; width: 30px; }
            QComboBox::down-arrow {
                image: none; border-left: 5px solid transparent; border-right: 5px solid transparent;
                border-top: 5px solid #94A3B8; margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #1E293B;
                color: white;
                selection-background-color: #3B82F6;
                border: 1px solid #334155;
            }
        """)

class SidebarButton(QPushButton):
    """כפתור תפריט צד כהה"""
    def __init__(self, text, icon_char):
        super().__init__()
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(55)
        self.text_val = text
        self.icon_val = icon_char
        self.update_style(False)

    def update_style(self, active):
        if active:
            self.setText(f"  {self.icon_val}   {self.text_val}")
            self.setStyleSheet("""
                QPushButton {
                    text-align: left; padding-left: 20px;
                    background-color: rgba(59, 130, 246, 0.15); 
                    color: #60A5FA; /* תכלת */
                    border-radius: 12px; font-weight: bold; font-size: 15px; border: none;
                    border-left: 4px solid #3B82F6;
                }
            """)
        else:
            self.setText(f"  {self.icon_val}   {self.text_val}")
            self.setStyleSheet("""
                QPushButton {
                    text-align: left; padding-left: 24px;
                    background-color: transparent; 
                    color: #94A3B8; /* אפור בהיר */
                    font-weight: 500; font-size: 15px; border: none;
                }
                QPushButton:hover { background-color: rgba(255, 255, 255, 0.05); color: #E2E8F0; }
            """)

class ProfileScreen(QWidget):
    def __init__(self, switch_callback):
        super().__init__()
        self.switch_callback = switch_callback
        self.setup_ui()

    def setup_ui(self):
        # רקע ראשי
        self.setStyleSheet("""
            QWidget {
                background-color: #0F172A; /* Deep Slate */
                font-family: 'Segoe UI';
            }
        """)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(60, 40, 60, 40)
        
        # --- הכרטיס הראשי (Main Card) ---
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1E293B; /* Slate 800 */
                border-radius: 24px;
                border: 1px solid #334155;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 15)
        card.setGraphicsEffect(shadow)
        
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # ==========================
        # 1. סרגל צד (Sidebar)
        # ==========================
        sidebar = QFrame()
        sidebar.setFixedWidth(300)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #0F172A; /* כהה יותר מהתוכן */
                border-top-left-radius: 24px; 
                border-bottom-left-radius: 24px;
                border-right: 1px solid #334155;
            }
        """)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(25, 50, 25, 50)
        sb_layout.setSpacing(15)

        # Avatar Section
        avatar_container = QFrame()
        avatar_container.setStyleSheet("background: transparent; border: none;")
        ac_layout = QVBoxLayout(avatar_container)
        
        self.avatar = QLabel("👾")
        self.avatar.setFixedSize(110, 110)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setStyleSheet("""
            background-color: rgba(59, 130, 246, 0.1);
            color: #E2E8F0; font-size: 60px;
            border-radius: 55px; 
            border: 3px solid #3B82F6;
        """)
        
        user_name_lbl = QLabel("Traveler One")
        user_name_lbl.setAlignment(Qt.AlignCenter)
        user_name_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: white; margin-top: 15px; border:none;")
        
        user_role_lbl = QLabel("Pro Member")
        user_role_lbl.setAlignment(Qt.AlignCenter)
        user_role_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #3B82F6; letter-spacing: 1px; border:none;")

        ac_layout.addWidget(self.avatar, alignment=Qt.AlignCenter)
        ac_layout.addWidget(user_name_lbl)
        ac_layout.addWidget(user_role_lbl)
        
        sb_layout.addWidget(avatar_container)
        sb_layout.addSpacing(40)

        # Navigation Buttons
        self.btn_account = SidebarButton("My Account", "👤")
        self.btn_security = SidebarButton("Security", "🔒")
        self.btn_prefs = SidebarButton("Preferences", "⚙️")
        
        self.btn_account.clicked.connect(lambda: self.switch_tab(0))
        self.btn_security.clicked.connect(lambda: self.switch_tab(1))
        self.btn_prefs.clicked.connect(lambda: self.switch_tab(2))

        sb_layout.addWidget(self.btn_account)
        sb_layout.addWidget(self.btn_security)
        sb_layout.addWidget(self.btn_prefs)
        
        sb_layout.addStretch()
        
        # Back Button
        btn_back = QPushButton("← Back to Menu")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet("""
            QPushButton { 
                color: #64748B; background: transparent; font-weight: 600; font-size: 14px; 
                border: none; text-align: center; 
            } 
            QPushButton:hover { color: #FFFFFF; }
        """)
        btn_back.clicked.connect(lambda: self.switch_callback(1))
        sb_layout.addWidget(btn_back)

        # ==========================
        # 2. אזור התוכן (Content Area)
        # ==========================
        content_area = QFrame()
        content_area.setStyleSheet("""
            QFrame {
                background-color: transparent; /* שקוף כדי לקבל את צבע הכרטיס */
                border: none;
            }
        """)
        ca_layout = QVBoxLayout(content_area)
        ca_layout.setContentsMargins(60, 60, 60, 60)
        
        self.stack = QStackedWidget()
        
        # --- Tab 1: Account ---
        page_account = QWidget()
        pa_layout = QVBoxLayout(page_account)
        pa_layout.setAlignment(Qt.AlignTop); pa_layout.setSpacing(30)
        
        pa_layout.addWidget(self.create_header("Personal Info", "Manage your personal details."))
        
        # Form Groups
        pa_layout.addWidget(self.create_label("Display Name"))
        pa_layout.addWidget(DarkInput("Enter your full name", icon_char="📛"))
        
        pa_layout.addWidget(self.create_label("Email Address"))
        pa_layout.addWidget(DarkInput("user@example.com", icon_char="📧"))
        
        pa_layout.addStretch()
        pa_layout.addWidget(self.create_action_button("Save Changes"))

        # --- Tab 2: Security ---
        page_security = QWidget()
        ps_layout = QVBoxLayout(page_security)
        ps_layout.setAlignment(Qt.AlignTop); ps_layout.setSpacing(30)
        
        ps_layout.addWidget(self.create_header("Security", "Keep your account safe."))
        
        ps_layout.addWidget(self.create_label("Current Password"))
        ps_layout.addWidget(DarkInput("••••••••", is_password=True, icon_char="🔑"))
        
        ps_layout.addWidget(self.create_label("New Password"))
        ps_layout.addWidget(DarkInput("Enter new password", is_password=True, icon_char="🔒"))
        
        ps_layout.addStretch()
        ps_layout.addWidget(self.create_action_button("Update Password"))

        # --- Tab 3: Preferences ---
        page_prefs = QWidget()
        pp_layout = QVBoxLayout(page_prefs)
        pp_layout.setAlignment(Qt.AlignTop); pp_layout.setSpacing(25)
        
        pp_layout.addWidget(self.create_header("Preferences", "Customize your app experience."))
        
        # Switches
        pp_layout.addWidget(self.create_switch_row("Dark Mode", "Always On (Pro Feature)", True))
        pp_layout.addWidget(self.create_switch_row("Email Notifications", "Get updates about trips", True))
        pp_layout.addWidget(self.create_switch_row("Auto-Save", "Save trip drafts automatically", True))
        
        # Combo
        pp_layout.addWidget(self.create_label("Currency"))
        combo = DarkComboBox()
        combo.addItems(["USD - US Dollar ($)", "ILS - Israeli Shekel (₪)", "EUR - Euro (€)"])
        pp_layout.addWidget(combo)
        
        pp_layout.addStretch()
        
        # Danger Zone (Red)
        danger_zone = QFrame()
        danger_zone.setStyleSheet("""
            background-color: rgba(239, 68, 68, 0.1); 
            border: 1px solid rgba(239, 68, 68, 0.3); 
            border-radius: 12px;
        """)
        dz_layout = QHBoxLayout(danger_zone); dz_layout.setContentsMargins(20, 15, 20, 15)
        
        lbl_danger = QLabel("Delete Account")
        lbl_danger.setStyleSheet("color: #EF4444; font-weight: 700; border: none; background: transparent;")
        
        btn_delete = QPushButton("Delete")
        btn_delete.setCursor(Qt.PointingHandCursor)
        btn_delete.setFixedSize(80, 35)
        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #EF4444; color: white; border-radius: 8px; font-weight: bold; border: none;
            }
            QPushButton:hover { background-color: #DC2626; }
        """)
        dz_layout.addWidget(lbl_danger); dz_layout.addStretch(); dz_layout.addWidget(btn_delete)
        pp_layout.addWidget(danger_zone)

        # Add pages to stack
        self.stack.addWidget(page_account)
        self.stack.addWidget(page_security)
        self.stack.addWidget(page_prefs)

        card_layout.addWidget(sidebar)
        card_layout.addWidget(content_area)
        
        ca_layout.addWidget(self.stack) # Important: Add stack to layout
        
        main_layout.addWidget(card)
        self.switch_tab(0)

    # --- Helpers ---

    def create_header(self, title, subtitle):
        w = QWidget()
        l = QVBoxLayout(w); l.setContentsMargins(0,0,0,0); l.setSpacing(5)
        t = QLabel(title); t.setStyleSheet("font-size: 28px; font-weight: 800; color: #FFFFFF; border:none;")
        s = QLabel(subtitle); s.setStyleSheet("font-size: 14px; color: #94A3B8; border:none;")
        l.addWidget(t); l.addWidget(s)
        return w

    def create_label(self, text):
        l = QLabel(text)
        l.setStyleSheet("font-size: 13px; font-weight: 700; color: #CBD5E1; margin-bottom: 4px; border:none;")
        return l

    def create_action_button(self, text):
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(50)
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #2563EB);
                color: white; font-weight: bold; font-size: 15px; border-radius: 12px; border:none;
            }
            QPushButton:hover { background: #1D4ED8; }
        """)
        return btn

    def create_switch_row(self, title, desc, active):
        w = QWidget()
        l = QHBoxLayout(w); l.setContentsMargins(0,0,0,0)
        
        txt_l = QVBoxLayout(); txt_l.setSpacing(2)
        t = QLabel(title); t.setStyleSheet("font-size: 15px; font-weight: 700; color: #F1F5F9; border: none; background: transparent;")
        d = QLabel(desc); d.setStyleSheet("font-size: 13px; color: #64748B; border: none; background: transparent;")
        txt_l.addWidget(t); txt_l.addWidget(d)
        
        sw = ModernSwitch(active)
        
        l.addLayout(txt_l); l.addStretch(); l.addWidget(sw)
        return w 

    def switch_tab(self, index):
        self.stack.setCurrentIndex(index)
        self.btn_account.update_style(index == 0)
        self.btn_security.update_style(index == 1)
        self.btn_prefs.update_style(index == 2)