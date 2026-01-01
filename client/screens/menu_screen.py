import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QColor, QLinearGradient, QPalette, QBrush

# --- רכיבים גרפיים (אותם רכיבים ממסך הכניסה) ---

class FloatingParticle(QFrame):
    """חלקיק מרחף ברקע"""
    def __init__(self, parent, x, y, size):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.move(x, y)
        self.setStyleSheet(f"""
            background-color: rgba(255, 255, 255, {random.randint(3, 10)});
            border-radius: {size // 2}px;
        """)
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(random.randint(15000, 30000))
        self.anim.setStartValue(QPoint(x, y))
        self.anim.setEndValue(QPoint(x, y - 200))
        self.anim.setEasingCurve(QEasingCurve.InOutSine)
        self.anim.setLoopCount(-1)
        self.anim.start()

class DashboardCard(QPushButton):
    """כרטיס פעולה גדול ומעוצב"""
    def __init__(self, title, desc, emoji, color_theme, callback):
        super().__init__()
        self.callback = callback
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(280, 340) # כרטיס גבוה ומרשים
        
        # שמירת צבעים
        self.normal_style = f"""
            QPushButton {{
                background-color: rgba(30, 41, 59, 0.7); /* כהה חצי שקוף */
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
        
        # צללית עדינה
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 40, 30, 40)
        layout.setSpacing(15)
        
        # 1. אייקון זוהר
        icon_circle = QLabel(emoji)
        icon_circle.setFixedSize(70, 70)
        icon_circle.setAlignment(Qt.AlignCenter)
        icon_circle.setStyleSheet(f"""
            background-color: {color_theme}15; 
            color: {color_theme};
            font-size: 32px;
            border-radius: 35px;
            border: 1px solid {color_theme}40;
        """)
        
        # 2. טקסטים
        lbl_title = QLabel(title)
        lbl_title.setWordWrap(True)
        lbl_title.setStyleSheet("font-size: 22px; font-weight: bold; color: white; background: transparent; border: none;")
        
        lbl_desc = QLabel(desc)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("font-size: 14px; color: #94A3B8; background: transparent; border: none; line-height: 1.4;")
        
        # 3. חץ אינדיקטור
        lbl_arrow = QLabel("➔")
        lbl_arrow.setAlignment(Qt.AlignRight)
        lbl_arrow.setStyleSheet(f"font-size: 24px; color: {color_theme}; background: transparent; border: none;")
        
        layout.addWidget(icon_circle)
        layout.addSpacing(10)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        layout.addStretch()
        layout.addWidget(lbl_arrow)
        
        self.clicked.connect(self.callback)

    def enterEvent(self, event):
        self.setStyleSheet(self.hover_style)
        # אנימציית ציפה למעלה
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(150)
        self.anim.setEndValue(self.pos() - QPoint(0, 8))
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.normal_style)
        # חזרה למקום
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(150)
        self.anim.setEndValue(self.pos() + QPoint(0, 8))
        self.anim.start()
        super().leaveEvent(event)

class MenuScreen(QWidget):
    def __init__(self, switch_callback):
        super().__init__()
        self.switch_callback = switch_callback
        self.username = "Traveler"
        self.setup_ui()
        self.create_particles()

    def create_particles(self):
        for _ in range(25):
            size = random.randint(5, 20)
            x = random.randint(0, 1000)
            y = random.randint(0, 800)
            p = FloatingParticle(self, x, y, size)
            p.lower() 

    def set_user(self, username):
        self.username = username
        self.header_title.setText(f"Hello, {username}")

    def setup_ui(self):
        # רקע זהה בדיוק למסך הכניסה (Deep Slate)
        self.setStyleSheet("""
            QWidget {
                background-color: #0F172A; 
                font-family: 'Segoe UI';
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(80, 60, 80, 60)
        
        # --- Header Section ---
        header = QHBoxLayout()
        
        text_layout = QVBoxLayout()
        self.header_title = QLabel(f"Hello, {self.username}")
        # שימוש בצבע לבן בוהק לכותרת
        self.header_title.setStyleSheet("font-size: 48px; font-weight: 800; color: #FFFFFF; background: transparent;")
        
        self.header_sub = QLabel("Where would you like to go today?")
        self.header_sub.setStyleSheet("font-size: 18px; color: #94A3B8; background: transparent;")
        
        text_layout.addWidget(self.header_title)
        text_layout.addWidget(self.header_sub)
        
        # כפתור התנתקות מעוצב
        btn_logout = QPushButton("Log Out")
        btn_logout.setCursor(Qt.PointingHandCursor)
        btn_logout.setFixedSize(110, 42)
        btn_logout.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.1);
                color: #EF4444;
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 21px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #EF4444;
                color: white;
            }
        """)
        # חזרה למסך 0 (Login)
        btn_logout.clicked.connect(lambda: self.switch_callback(0))
        
        header.addLayout(text_layout)
        header.addStretch()
        header.addWidget(btn_logout, alignment=Qt.AlignTop)
        
        main_layout.addLayout(header)
        main_layout.addSpacing(60)

        # --- Cards Grid ---
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(40)
        
        # כרטיס 1: תכנון טיול (Hero Card) - כחול
        self.card_new = DashboardCard(
            title="Plan New Trip",
            desc="Let our AI architect design your perfect itinerary with flights & hotels.",
            emoji="✨",
            color_theme="#3B82F6", 
            callback=lambda: self.switch_callback(2) # מסך טופס טיול
        )
        
        # כרטיס 2: היסטוריה - ירוק/טורקיז
        self.card_history = DashboardCard(
            title="My Journeys",
            desc="Access your past adventures and saved itineraries.",
            emoji="🌍",
            color_theme="#10B981", 
            callback=lambda: self.switch_callback(4) # מסך היסטוריה
        )
        
        # כרטיס 3: פרופיל - סגול
        self.card_profile = DashboardCard(
            title="My Profile",
            desc="Manage your account, preferences, and security settings.",
            emoji="👤",
            color_theme="#8B5CF6", 
            callback=lambda: self.switch_callback(5) # --> חיבור למסך הפרופיל החדש!
        )
        
        cards_layout.addWidget(self.card_new)
        cards_layout.addWidget(self.card_history)
        cards_layout.addWidget(self.card_profile)
        cards_layout.addStretch()
        
        main_layout.addLayout(cards_layout)
        main_layout.addStretch()
        
        # --- Footer ---
        footer = QLabel("Powered by Gemini 2.5 Hybrid-AI Engine")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #334155; font-size: 12px; font-weight: 600; background: transparent;")
        main_layout.addWidget(footer)