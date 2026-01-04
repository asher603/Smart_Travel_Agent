from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
    QMessageBox, QFrame, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal

class AuthView(QWidget):
    # Signals that the Presenter will listen to
    login_signal = Signal(str, str)   # username, password
    register_signal = Signal(str, str) # username, password

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Travel Agent - Login")
        self.resize(350, 500)
        self.init_ui()

    def init_ui(self):
        # Main Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # 1. Title / Logo Area
        title = QLabel("Smart Travel")
        title.setObjectName("h1") # For CSS styling
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("AI-Powered Trip Planner")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # 2. Input Fields
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        # 3. Action Buttons (THE MISSING PART)
        self.btn_login_action = QPushButton("Login")
        self.btn_login_action.setObjectName("primaryButton")
        layout.addWidget(self.btn_login_action)

        self.btn_register_action = QPushButton("Create Account")
        self.btn_register_action.setObjectName("secondaryButton")
        layout.addWidget(self.btn_register_action)

        # Spacer to push everything up
        layout.addStretch()

        self.setLayout(layout)

        # 4. Connect Buttons to Internal Methods
        # Now this works because the buttons exist!
        self.btn_login_action.clicked.connect(self._on_login_click)
        self.btn_register_action.clicked.connect(self._on_register_click)

    def _on_login_click(self):
        """ Collects input and emits signal to Presenter """
        u = self.username_input.text()
        p = self.password_input.text()
        if not u or not p:
            self.show_error("Please enter both username and password")
            return
        self.login_signal.emit(u, p)

    def _on_register_click(self):
        """ Collects input and emits signal to Presenter """
        u = self.username_input.text()
        p = self.password_input.text()
        if not u or not p:
            self.show_error("Please enter a username and password to register")
            return
        self.register_signal.emit(u, p)

    def show_error(self, message):
        QMessageBox.warning(self, "Error", message)

    def show_success(self, message):
        QMessageBox.information(self, "Success", message)