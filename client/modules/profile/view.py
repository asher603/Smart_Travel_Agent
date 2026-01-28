import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, 
    QMessageBox, QLineEdit, QSizePolicy
)
from PySide6.QtCore import Qt, Signal

# ============================================================================
# Custom Styled Widgets - Reusable components
# ============================================================================

class GlassFrame(QFrame):
    """Base frame with glass (semi-transparent) styling"""
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)

class StyledInput(QLineEdit):
    """Glass-styled text input field"""
    def __init__(self, placeholder, is_password=False):
        super().__init__()
        self.setPlaceholderText(placeholder)
        if is_password:
            self.setEchoMode(QLineEdit.Password)
        
        self.setFixedHeight(45)
        
        # Input field styling
        self.setStyleSheet("""
            QLineEdit {
                background-color: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 0 15px;
                font-size: 14px;
                color: white;
            }
            QLineEdit:focus {
                border: 1px solid #42a5f5;
                background-color: rgba(0, 0, 0, 0.3);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.4);
            }
        """)

# ============================================================================
# Main Profile View Class
# ============================================================================

class ProfileView(QWidget):
    # Signals for external communication (to Presenter)
    back_signal = Signal()
    logout_signal = Signal()
    save_identity_signal = Signal(dict)
    change_pass_signal = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Build the user interface"""
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---------------------------------------------------------
        # 1. Header Area
        # ---------------------------------------------------------
        header = QFrame()
        header.setFixedHeight(140)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1565c0, stop:1 #0d47a1);
                border-bottom-left-radius: 30px;
                border-bottom-right-radius: 30px;
            }
        """)
        
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(25, 15, 25, 15)

        # Back button
        top_bar = QHBoxLayout()
        self.btn_back = QPushButton("🔙 Back")
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.setStyleSheet("color: white; border: none; font-weight: bold; font-size: 14px; text-align: left;")
        self.btn_back.clicked.connect(self.back_signal.emit)
        top_bar.addWidget(self.btn_back)
        top_bar.addStretch()
        header_layout.addLayout(top_bar)

        # User details
        user_info = QHBoxLayout()
        user_info.setSpacing(15)
        
        self.avatar = QLabel("👤")
        self.avatar.setFixedSize(60, 60)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setStyleSheet("""
            font-size: 30px; 
            background: rgba(255,255,255,0.2); 
            border-radius: 30px;
            color: white;
        """)
        
        name_layout = QVBoxLayout()
        self.lbl_name = QLabel("Guest")  # Will be replaced on load
        self.lbl_name.setStyleSheet("font-size: 24px; font-weight: bold; color: white; background: transparent;")
        
        self.lbl_role = QLabel("Account Settings")
        self.lbl_role.setStyleSheet("font-size: 14px; color: #bbdefb; background: transparent;")
        
        name_layout.addWidget(self.lbl_name)
        name_layout.addWidget(self.lbl_role)
        
        user_info.addWidget(self.avatar)
        user_info.addLayout(name_layout)
        user_info.addStretch()
        
        header_layout.addLayout(user_info)
        main_layout.addWidget(header)

        # ---------------------------------------------------------
        # 2. Main Content
        # ---------------------------------------------------------
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 30, 40, 30)
        content_layout.setSpacing(25)

        # --- Email Card ---
        email_card = GlassFrame()
        ec_layout = QVBoxLayout(email_card)
        ec_layout.setContentsMargins(20, 20, 20, 20)
        
        ec_layout.addWidget(QLabel("📧 Contact Information"))
        self.inp_email = StyledInput("Email Address")
        ec_layout.addWidget(self.inp_email)
        
        self.btn_update_email = QPushButton("Update Email")
        self.btn_update_email.setCursor(Qt.PointingHandCursor)
        self.btn_update_email.setFixedHeight(40)
        self.btn_update_email.setStyleSheet("""
            QPushButton { background: #1976d2; color: white; border-radius: 8px; font-weight: bold; border: none; }
            QPushButton:hover { background: #1565c0; }
        """)
        self.btn_update_email.clicked.connect(self.on_save_identity_click)
        ec_layout.addWidget(self.btn_update_email)
        
        content_layout.addWidget(email_card)

        # --- Password Card ---
        pass_card = GlassFrame()
        pc_layout = QVBoxLayout(pass_card)
        pc_layout.setContentsMargins(20, 20, 20, 20)
        
        pc_layout.addWidget(QLabel("🔒 Security"))
        
        self.inp_old_pass = StyledInput("Current Password", is_password=True)
        pc_layout.addWidget(self.inp_old_pass)
        
        self.inp_new_pass = StyledInput("New Password", is_password=True)
        pc_layout.addWidget(self.inp_new_pass)
        
        self.btn_change_pass = QPushButton("Change Password")
        self.btn_change_pass.setCursor(Qt.PointingHandCursor)
        self.btn_change_pass.setFixedHeight(40)
        self.btn_change_pass.setStyleSheet("""
            QPushButton { background: #fb8c00; color: white; border-radius: 8px; font-weight: bold; border: none; }
            QPushButton:hover { background: #f57c00; }
        """)
        self.btn_change_pass.clicked.connect(self.on_change_pass_click)
        pc_layout.addWidget(self.btn_change_pass)
        
        content_layout.addWidget(pass_card)
        
        content_layout.addStretch()

        # --- Logout Button ---
        self.btn_logout = QPushButton("🚪 Log Out")
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        self.btn_logout.setFixedHeight(45)
        self.btn_logout.setStyleSheet("""
            QPushButton { 
                background: transparent; border: 1px solid #ef5350; color: #ef5350; border-radius: 10px; font-weight: bold; 
            }
            QPushButton:hover { background: rgba(239, 83, 80, 0.1); }
        """)
        self.btn_logout.clicked.connect(self.logout_signal.emit)
        content_layout.addWidget(self.btn_logout)

        main_layout.addWidget(content_widget)

    # --- Internal Logic Functions ---
    def on_save_identity_click(self):
        data = {"email": self.inp_email.text()}
        self.save_identity_signal.emit(data)

    def on_change_pass_click(self):
        self.change_pass_signal.emit(self.inp_old_pass.text(), self.inp_new_pass.text())

    def update_view(self, data):
        """Receives data and updates the screen"""
        
        # 1. Update username in header (if available)
        if "username" in data and data["username"]:
            self.lbl_name.setText(data["username"].capitalize())

        # 2. Update email field
        if "email" in data:
            new_email = data["email"]
            # Only update if data is not empty and (field is empty or user isn't typing)
            # This prevents server response from overwriting what user is currently typing
            if new_email is not None:
                if self.inp_email.text() == "" or not self.inp_email.hasFocus():
                    self.inp_email.setText(new_email)