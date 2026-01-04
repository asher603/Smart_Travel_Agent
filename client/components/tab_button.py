from PySide6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class TabButton(QPushButton):
    """Switchable Tab Button"""
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