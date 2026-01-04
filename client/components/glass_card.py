from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QColor


class GlassCard(QFrame):
    """A translucent card container"""
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setColor(QColor(0,0,0,50)); shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
