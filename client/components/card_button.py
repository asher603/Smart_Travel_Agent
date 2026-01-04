from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation, QPoint
from PySide6.QtGui import QColor

class CardButton(QPushButton):
    """Specific widget for the Dashboard Grid"""
    def __init__(self, title, desc, emoji, color_theme):
        super().__init__()
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(280, 340)
        
        # Styles
        self.normal_style = f"""
            QPushButton {{
                background-color: rgba(30, 41, 59, 0.7);
                border: 1px solid rgba(255,255,255,0.05);
                border-radius: 24px;
                text-align: left;
            }}
        """
        self.hover_style = f"""
            QPushButton {{
                background-color: rgba(30, 41, 59, 0.9);
                border: 1px solid {color_theme};
                border-radius: 24px;
                text-align: left;
            }}
        """
        self.setStyleSheet(self.normal_style)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setColor(QColor(0, 0, 0, 50)); shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 40, 30, 40)
        layout.setSpacing(15)
        
        # Icon
        icon_circle = QLabel(emoji)
        icon_circle.setFixedSize(70, 70)
        icon_circle.setAlignment(Qt.AlignCenter)
        icon_circle.setStyleSheet(f"""
            background-color: {color_theme}15; color: {color_theme};
            font-size: 32px; border-radius: 35px; border: 1px solid {color_theme}40; background: transparent;
        """)
        
        # Text
        lbl_title = QLabel(title)
        lbl_title.setWordWrap(True)
        lbl_title.setStyleSheet("font-size: 22px; font-weight: bold; color: white; background: transparent; border: none;")
        
        lbl_desc = QLabel(desc)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("font-size: 14px; color: #94A3B8; background: transparent; border: none; line-height: 1.4;")
        
        # Arrow
        lbl_arrow = QLabel("➔")
        lbl_arrow.setAlignment(Qt.AlignRight)
        lbl_arrow.setStyleSheet(f"font-size: 24px; color: {color_theme}; background: transparent; border: none;")
        
        layout.addWidget(icon_circle)
        layout.addSpacing(10)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        layout.addStretch()
        layout.addWidget(lbl_arrow)

    def enterEvent(self, event):
        self.setStyleSheet(self.hover_style)
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(150)
        self.anim.setEndValue(self.pos() - QPoint(0, 8))
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.normal_style)
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(150)
        self.anim.setEndValue(self.pos() + QPoint(0, 8))
        self.anim.start()
        super().leaveEvent(event)