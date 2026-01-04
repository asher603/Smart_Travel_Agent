import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton
)
from PySide6.QtCore import Qt, Signal
from components import ( 
    FloatingParticle, CardButton 
)

class DashboardView(QWidget):
    # MVP Signals: View tells Presenter "User wants to do X"
    logout_requested = Signal()
    plan_trip_requested = Signal()
    history_requested = Signal()
    profile_requested = Signal()

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.create_particles()

    def create_particles(self):
        for _ in range(25):
            size = random.randint(5, 20)
            x = random.randint(0, 1000)
            y = random.randint(0, 800)
            p = FloatingParticle(self, x, y, size)
            p.lower() 

    def init_ui(self):
        self.setStyleSheet("QWidget { background-color: #0F172A; font-family: 'Segoe UI'; }")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(80, 60, 80, 60)
        
        # --- Header ---
        header = QHBoxLayout()
        text_layout = QVBoxLayout()
        
        self.header_title = QLabel("Hello, Traveler")
        self.header_title.setStyleSheet("font-size: 48px; font-weight: 800; color: #FFFFFF; background: transparent;")
        
        sub_title = QLabel("Where would you like to go today?")
        sub_title.setStyleSheet("font-size: 18px; color: #94A3B8; background: transparent;")
        
        text_layout.addWidget(self.header_title)
        text_layout.addWidget(sub_title)
        
        # Logout Button
        btn_logout = QPushButton("Log Out")
        btn_logout.setCursor(Qt.PointingHandCursor)
        btn_logout.setFixedSize(110, 42)
        btn_logout.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.1); color: #EF4444;
                border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 21px;
                font-weight: 600; font-size: 14px;
            }
            QPushButton:hover { background-color: #EF4444; color: white; }
        """)
        btn_logout.clicked.connect(self.logout_requested.emit)
        
        header.addLayout(text_layout)
        header.addStretch()
        header.addWidget(btn_logout, alignment=Qt.AlignTop)
        
        main_layout.addLayout(header)
        main_layout.addSpacing(60)

        # --- Cards ---
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(40)
        
        self.card_new = CardButton("Plan New Trip", "Let our AI architect design your perfect itinerary.", "✨", "#3B82F6")
        self.card_new.clicked.connect(self.plan_trip_requested.emit)
        
        self.card_history = CardButton("My Journeys", "Access your past adventures and saved itineraries.", "🌍", "#10B981")
        self.card_history.clicked.connect(self.history_requested.emit)

        self.card_profile = CardButton("My Profile", "Manage your account, preferences, and security.", "👤", "#8B5CF6")
        self.card_profile.clicked.connect(self.profile_requested.emit)
        
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

    def set_username_display(self, name):
        self.header_title.setText(f"Hello, {name}")