from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PySide6.QtCore import Qt, Signal

class ModernInput(QFrame):
    """Styled input field with icon and eye button"""
    returnPressed = Signal() 

    def __init__(self, placeholder="", is_password=False, icon_char=""):
        super().__init__()
        self.setFixedHeight(55)
        self.setStyleSheet(self._style(focused=False))
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(10)
        
        if icon_char:
            self.icon_lbl = QLabel(icon_char)
            self.icon_lbl.setStyleSheet("border: none; background: transparent; font-size: 18px; color: #94A3B8;")
            layout.addWidget(self.icon_lbl)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(placeholder)
        self.input_field.setStyleSheet("""
            QLineEdit { border: none; background: transparent; font-size: 15px; color: #1E293B; font-family: 'Segoe UI'; }
            QLineEdit::placeholder { color: #94A3B8; }
        """)
        self.input_field.returnPressed.connect(self.returnPressed.emit)
        
        self.input_field.focusInEvent = self._on_focus
        self.input_field.focusOutEvent = self._on_blur
        
        layout.addWidget(self.input_field)

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