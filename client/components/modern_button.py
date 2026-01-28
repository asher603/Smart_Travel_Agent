from PySide6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QCursor

class ModernButton(QPushButton):
    def __init__(self, text, color="#00f2ff", parent=None):
        super().__init__(text, parent)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.default_color = color
        self._setup_style()

    def _setup_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.default_color};
                color: black;
                border-radius: 15px;
                font-weight: bold;
                font-size: 14px;
                border: none;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: white;
            }}
            QPushButton:pressed {{
                background-color: {self.default_color};
                padding-top: 12px;
                padding-left: 22px;
            }}
        """)
        # Glow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(self.default_color))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)