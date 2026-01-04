import random
from PySide6.QtWidgets import QFrame
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QColor

class FloatingParticle(QFrame):
    """Floating particle animation"""
    def __init__(self, parent, x, y, size):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.move(x, y)
        self.setStyleSheet(f"""
            background-color: rgba(255, 255, 255, {random.randint(10, 30)});
            border-radius: {size // 2}px;
        """)
        
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(random.randint(5000, 10000))
        self.anim.setStartValue(QPoint(x, y))
        self.anim.setEndValue(QPoint(x, y - 100)) 
        self.anim.setEasingCurve(QEasingCurve.InOutSine)
        self.anim.setLoopCount(-1) 
        self.anim.start()