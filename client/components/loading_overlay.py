"""
AI Loading Overlay - Animated loading screen for trip generation
Displays animated progress while AI agent processes the request
"""
import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, 
    QPoint, QSequentialAnimationGroup, QParallelAnimationGroup,
    Property
)
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QLinearGradient


class SpinnerRing(QWidget):
    """Animated spinning ring with gradient"""
    def __init__(self, parent=None, size=120, ring_width=6):
        super().__init__(parent)
        self._rotation = 0
        self._size = size
        self._ring_width = ring_width
        self.setFixedSize(size, size)
        
        # Animation
        self.anim = QPropertyAnimation(self, b"rotation")
        self.anim.setDuration(1500)
        self.anim.setStartValue(0)
        self.anim.setEndValue(360)
        self.anim.setLoopCount(-1)
        self.anim.setEasingCurve(QEasingCurve.Linear)
        
    def get_rotation(self):
        return self._rotation
    
    def set_rotation(self, value):
        self._rotation = value
        self.update()
    
    rotation = Property(float, get_rotation, set_rotation)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Translate and rotate
        center = self._size // 2
        painter.translate(center, center)
        painter.rotate(self._rotation)
        
        # Create gradient arc
        gradient = QLinearGradient(-center, 0, center, 0)
        gradient.setColorAt(0, QColor("#3B82F6"))
        gradient.setColorAt(0.5, QColor("#8B5CF6"))
        gradient.setColorAt(1, QColor("#EC4899"))
        
        pen = QPen(gradient, self._ring_width)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        # Draw arc (270 degrees)
        radius = center - self._ring_width
        painter.drawArc(-radius, -radius, radius * 2, radius * 2, 0, 270 * 16)
        
    def start(self):
        self.anim.start()
        
    def stop(self):
        self.anim.stop()


class PulsingDot(QFrame):
    """Single pulsing dot for the loading indicator"""
    def __init__(self, parent=None, delay=0):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self._base_style = """
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                stop:0 #3B82F6, stop:1 #8B5CF6);
            border-radius: 6px;
        """
        self.setStyleSheet(self._base_style)
        
        # Opacity effect
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0.3)
        self.setGraphicsEffect(self.opacity_effect)
        
        # Animation
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(600)
        self.anim.setStartValue(0.3)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.InOutSine)
        
        # Reverse animation
        self.anim_reverse = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_reverse.setDuration(600)
        self.anim_reverse.setStartValue(1.0)
        self.anim_reverse.setEndValue(0.3)
        self.anim_reverse.setEasingCurve(QEasingCurve.InOutSine)
        
        # Sequence
        self.group = QSequentialAnimationGroup()
        self.group.addAnimation(self.anim)
        self.group.addAnimation(self.anim_reverse)
        self.group.setLoopCount(-1)
        
        # Delay start
        QTimer.singleShot(delay, self.start)
        
    def start(self):
        self.group.start()
        
    def stop(self):
        self.group.stop()


class FloatingIcon(QLabel):
    """Floating travel icon for background ambiance"""
    def __init__(self, parent, icon, x, y, size=24):
        super().__init__(icon, parent)
        self.setStyleSheet(f"""
            font-size: {size}px;
            background: transparent;
        """)
        self.move(x, y)
        self._start_y = y
        
        # Float animation
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(random.randint(3000, 5000))
        self.anim.setStartValue(QPoint(x, y))
        self.anim.setEndValue(QPoint(x, y - random.randint(20, 40)))
        self.anim.setEasingCurve(QEasingCurve.InOutSine)
        self.anim.setLoopCount(-1)
        
        # Opacity
        self.opacity = QGraphicsOpacityEffect(self)
        self.opacity.setOpacity(random.uniform(0.1, 0.3))
        self.setGraphicsEffect(self.opacity)
        
    def start(self):
        self.anim.start()
        
    def stop(self):
        self.anim.stop()


class LoadingOverlay(QWidget):
    """Full-screen loading overlay with animations"""
    
    LOADING_MESSAGES = [
        ("🔍", "Analyzing your preferences..."),
        ("🗺️", "Mapping out destinations..."),
        ("✈️", "Finding the best flights..."),
        ("🏨", "Searching for accommodations..."),
        ("🍽️", "Discovering local cuisine..."),
        ("📸", "Locating must-see attractions..."),
        ("📅", "Creating your itinerary..."),
        ("💰", "Optimizing your budget..."),
        ("🎯", "Personalizing recommendations..."),
        ("✨", "Adding finishing touches..."),
    ]
    
    TRAVEL_ICONS = ["✈️", "🌍", "🗺️", "🏖️", "🏔️", "🌴", "🎒", "📸", "🚀", "⭐", "🌟", "💫"]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.message_index = 0
        self.floating_icons = []
        self.setup_ui()
        self.hide()
        
    def setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background: rgba(15, 23, 42, 0.95);
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Center container
        self.container = QFrame()
        self.container.setFixedSize(400, 350)
        self.container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(30, 41, 59, 0.9),
                    stop:1 rgba(15, 23, 42, 0.95));
                border-radius: 24px;
                border: 1px solid rgba(59, 130, 246, 0.3);
            }
        """)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setColor(QColor(59, 130, 246, 80))
        shadow.setOffset(0, 15)
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setAlignment(Qt.AlignCenter)
        container_layout.setSpacing(24)
        container_layout.setContentsMargins(40, 40, 40, 40)
        
        # Spinner
        self.spinner = SpinnerRing(size=100, ring_width=5)
        container_layout.addWidget(self.spinner, alignment=Qt.AlignCenter)
        
        # AI Icon in center of spinner
        self.ai_icon = QLabel("🤖")
        self.ai_icon.setStyleSheet("""
            font-size: 36px;
            background: transparent;
        """)
        self.ai_icon.setParent(self.spinner)
        self.ai_icon.move(32, 32)
        
        # Title
        self.title = QLabel("AI Agent Working")
        self.title.setStyleSheet("""
            font-size: 22px;
            font-weight: 700;
            color: white;
            background: transparent;
        """)
        self.title.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.title)
        
        # Message with icon
        self.message_container = QFrame()
        self.message_container.setStyleSheet("background: transparent;")
        message_layout = QVBoxLayout(self.message_container)
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(8)
        
        self.message_icon = QLabel("🔍")
        self.message_icon.setStyleSheet("""
            font-size: 28px;
            background: transparent;
        """)
        self.message_icon.setAlignment(Qt.AlignCenter)
        message_layout.addWidget(self.message_icon)
        
        self.message = QLabel("Analyzing your preferences...")
        self.message.setStyleSheet("""
            font-size: 15px;
            font-weight: 500;
            color: #94A3B8;
            background: transparent;
        """)
        self.message.setAlignment(Qt.AlignCenter)
        message_layout.addWidget(self.message)
        
        container_layout.addWidget(self.message_container)
        
        # Pulsing dots
        dots_frame = QFrame()
        dots_frame.setStyleSheet("background: transparent;")
        dots_layout = QVBoxLayout(dots_frame)
        dots_layout.setContentsMargins(0, 10, 0, 0)
        
        dots_row = QFrame()
        dots_row.setStyleSheet("background: transparent;")
        dots_row_layout = QVBoxLayout(dots_row)
        dots_row_layout.setSpacing(8)
        
        # Create horizontal dot container
        from PySide6.QtWidgets import QHBoxLayout
        dots_h = QFrame()
        dots_h.setStyleSheet("background: transparent;")
        dots_h_layout = QHBoxLayout(dots_h)
        dots_h_layout.setSpacing(8)
        dots_h_layout.setContentsMargins(0, 0, 0, 0)
        
        self.dots = []
        for i in range(3):
            dot = PulsingDot(delay=i * 200)
            self.dots.append(dot)
            dots_h_layout.addWidget(dot)
        
        dots_h_layout.setAlignment(Qt.AlignCenter)
        dots_row_layout.addWidget(dots_h)
        dots_layout.addWidget(dots_row)
        container_layout.addWidget(dots_frame)
        
        layout.addWidget(self.container)
        
        # Message timer
        self.message_timer = QTimer()
        self.message_timer.timeout.connect(self.cycle_message)
        
    def create_floating_icons(self):
        """Create floating travel icons in background"""
        # Clear existing
        for icon in self.floating_icons:
            icon.stop()
            icon.deleteLater()
        self.floating_icons.clear()
        
        # Create new icons
        for _ in range(15):
            icon = random.choice(self.TRAVEL_ICONS)
            x = random.randint(50, self.width() - 100)
            y = random.randint(50, self.height() - 100)
            size = random.randint(20, 40)
            
            floating = FloatingIcon(self, icon, x, y, size)
            floating.start()
            floating.lower()  # Send to back
            self.floating_icons.append(floating)
            
    def cycle_message(self):
        """Cycle through loading messages"""
        self.message_index = (self.message_index + 1) % len(self.LOADING_MESSAGES)
        icon, text = self.LOADING_MESSAGES[self.message_index]
        
        # Fade out effect simulation
        self.message_icon.setText(icon)
        self.message.setText(text)
        
    def show_loading(self):
        """Start the loading animation"""
        self.message_index = 0
        icon, text = self.LOADING_MESSAGES[0]
        self.message_icon.setText(icon)
        self.message.setText(text)
        
        self.resize(self.parent().size())
        self.raise_()
        self.show()
        
        # Start animations
        self.spinner.start()
        for dot in self.dots:
            dot.start()
        
        # Create floating icons
        self.create_floating_icons()
        
        # Start message cycling
        self.message_timer.start(2500)
        
    def hide_loading(self):
        """Stop and hide the loading animation"""
        self.message_timer.stop()
        self.spinner.stop()
        
        for dot in self.dots:
            dot.stop()
            
        for icon in self.floating_icons:
            icon.stop()
            
        self.hide()
        
    def resizeEvent(self, event):
        """Handle resize to keep overlay fullscreen"""
        super().resizeEvent(event)
        # Reposition container in center
        if self.container:
            self.container.move(
                (self.width() - self.container.width()) // 2,
                (self.height() - self.container.height()) // 2
            )
