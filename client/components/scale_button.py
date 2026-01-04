from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt

class ScaleButton(QPushButton):
    """Button with tactile press effect"""
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
        self.setStyleSheet(self.default_style + "QPushButton { margin: 2px; }")
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.setStyleSheet(self.default_style + "QPushButton { margin: 0px; }")
        super().mouseReleaseEvent(e)