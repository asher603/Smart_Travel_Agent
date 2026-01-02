import random
from PySide6.QtWidgets import (
    QPushButton, QFrame, QLabel, QLineEdit, QHBoxLayout, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, Signal
from PySide6.QtGui import QColor, QPainter, QBrush

# --- 1. Card Component ---
class Card(QFrame):
    """כרטיס מעוצב עם צללית (משמש את TripScreen)"""
    def __init__(self, shadow=True):
        super().__init__()
        self.setObjectName("Card")
        if shadow:
            eff = QGraphicsDropShadowEffect(self)
            eff.setBlurRadius(20)
            eff.setXOffset(0)
            eff.setYOffset(5)
            eff.setColor(QColor(0,0,0,30))
            self.setGraphicsEffect(eff)

# --- 2. Floating Particle (Background Animation) ---
class FloatingParticle(QFrame):
    def __init__(self, parent, x, y, size):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.move(x, y)
        self.setStyleSheet(f"""
            background-color: rgba(255, 255, 255, {random.randint(5, 15)});
            border-radius: {size // 2}px;
        """)
        
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(random.randint(10000, 20000))
        self.anim.setStartValue(QPoint(x, y))
        self.anim.setEndValue(QPoint(x, y - 150))
        self.anim.setEasingCurve(QEasingCurve.InOutSine)
        self.anim.setLoopCount(-1)
        self.anim.start()

# --- 3. Modern Input (Text Field) ---
class ModernInput(QFrame):
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

# --- 4. Scale Button (Animated Button) ---
class ScaleButton(QPushButton):
    def __init__(self, text, bg_start="#3B82F6", bg_end="#2563EB"):
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
        self.setStyleSheet(self.default_style + "QPushButton { margin: 2px; }")
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.setStyleSheet(self.default_style + "QPushButton { margin: 0px; }")
        super().mouseReleaseEvent(e)

# --- 5. Modern Switch (Toggle Button) ---
class ModernSwitch(QPushButton):
    def __init__(self, active=False):
        super().__init__()
        self.setCheckable(True)
        self.setChecked(active)
        self.setFixedSize(50, 28)
        self.setCursor(Qt.PointingHandCursor)
        
    def hitButton(self, pos):
        return self.contentsRect().contains(pos)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.isChecked():
            bg_color = QColor("#3B82F6")
        else:
            bg_color = QColor("#CBD5E1")
            
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 14, 14)
        
        painter.setBrush(QBrush(Qt.white))
        circle_x = 24 if self.isChecked() else 4 
        painter.drawEllipse(circle_x, 4, 20, 20)
        painter.end()