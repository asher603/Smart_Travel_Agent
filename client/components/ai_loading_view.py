"""
AI Loading View - Simple & Clean
Shows user the system is working
"""
import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QColor, QPainter, QPen, QConicalGradient

from components.floating_particle import FloatingParticle


class Spinner(QWidget):
    """Simple spinning loader"""
    def __init__(self, parent=None, size=50):
        super().__init__(parent)
        self._angle = 0
        self._size = size
        self.setFixedSize(size, size)
        
        self.anim = QPropertyAnimation(self, b"angle")
        self.anim.setDuration(1000)
        self.anim.setStartValue(0)
        self.anim.setEndValue(360)
        self.anim.setLoopCount(-1)
        self.anim.setEasingCurve(QEasingCurve.Linear)
        
    def get_angle(self):
        return self._angle
    
    def set_angle(self, value):
        self._angle = value
        self.update()
    
    angle = Property(float, get_angle, set_angle)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center = self._size // 2
        painter.translate(center, center)
        painter.rotate(self._angle)
        
        gradient = QConicalGradient(0, 0, 0)
        gradient.setColorAt(0.0, QColor("#3B82F6"))
        gradient.setColorAt(0.7, QColor("#3B82F6"))
        gradient.setColorAt(1.0, QColor(59, 130, 246, 0))
        
        pen = QPen(gradient, 4)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        r = center - 4
        painter.drawArc(-r, -r, r * 2, r * 2, 0, 270 * 16)
        
    def start(self):
        self.anim.start()
        
    def stop(self):
        self.anim.stop()


class AIAgentLoadingView(QWidget):
    """Minimal loading screen"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.particles = []
        self.elapsed = 0
        self.dots = 0
        self.setup_ui()
        self.hide()
        
    def setup_ui(self):
        self.setStyleSheet("background: #0F172A;")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Card
        card = QFrame()
        card.setFixedSize(320, 200)
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 16px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setSpacing(20)
        
        # Spinner
        self.spinner = Spinner(size=50)
        card_layout.addWidget(self.spinner, alignment=Qt.AlignCenter)
        
        # Text
        self.label = QLabel("Creating your trip...")
        self.label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #1E293B;
        """)
        self.label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.label)
        
        # Time
        self.time_label = QLabel("0s")
        self.time_label.setStyleSheet("""
            font-size: 13px;
            color: #94A3B8;
        """)
        self.time_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.time_label)
        
        layout.addWidget(card)
        
        # Timers
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        
    def _tick(self):
        self.elapsed += 1
        self.dots = (self.dots + 1) % 4
        
        dots_str = "." * self.dots
        self.label.setText(f"Creating your trip{dots_str}")
        
        mins = self.elapsed // 60
        secs = self.elapsed % 60
        if mins:
            self.time_label.setText(f"{mins}m {secs}s")
        else:
            self.time_label.setText(f"{secs}s")
        
    def _create_particles(self):
        for p in self.particles:
            p.deleteLater()
        self.particles.clear()
        
        for _ in range(8):
            size = random.randint(4, 10)
            x = random.randint(0, self.width())
            y = random.randint(0, self.height())
            p = FloatingParticle(self, x, y, size)
            p.lower()
            self.particles.append(p)
        
    def show_loading(self, title="Creating your trip", subtitle=""):
        self.elapsed = 0
        self.dots = 0
        self.label.setText(f"{title}...")
        self.time_label.setText("0s")
        
        if self.parent():
            self.resize(self.parent().size())
        
        self.raise_()
        self.show()
        self.spinner.start()
        self._create_particles()
        self.timer.start(1000)
        
    def hide_loading(self):
        self.timer.stop()
        self.spinner.stop()
        self.hide()
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
