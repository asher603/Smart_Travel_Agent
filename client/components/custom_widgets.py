from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor

class Card(QFrame):
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