import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QScrollArea, QFrame, QPushButton, QMessageBox, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from components import FloatingParticle, ScaleButton

class TripHistoryCard(QFrame):
    """A styled card for a single history item"""
    clicked = Signal(str) # Emits trip_id
    delete_clicked = Signal(str)

    def __init__(self, trip_id, destination, date_str, budget_str):
        super().__init__()
        self.trip_id = trip_id
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(90)
        self.setStyleSheet("""
            QFrame {
                background-color: white; border-radius: 15px; border: 1px solid #E2E8F0;
            }
            QFrame:hover { border: 1px solid #3B82F6; background-color: #F8FAFC; }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)

        # Icon
        icon = QLabel("✈️")
        icon.setStyleSheet("font-size: 24px; border: none; background: transparent;")
        
        # Text Info
        info_layout = QVBoxLayout()
        lbl_dest = QLabel(destination)
        lbl_dest.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B; border: none; background: transparent;")
        
        lbl_meta = QLabel(f"{date_str}  •  Budget: {budget_str}")
        lbl_meta.setStyleSheet("font-size: 14px; color: #64748B; border: none; background: transparent;")
        
        info_layout.addWidget(lbl_dest)
        info_layout.addWidget(lbl_meta)
        
        # Delete Button
        btn_del = QPushButton("🗑️")
        btn_del.setFixedSize(40, 40)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet("""
            QPushButton { background: rgba(239, 68, 68, 0.1); border-radius: 10px; border: none; color: #DC2626; font-size: 18px; }
            QPushButton:hover { background: #DC2626; color: white; }
        """)
        btn_del.clicked.connect(self._on_del)

        layout.addWidget(icon)
        layout.addSpacing(15)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addWidget(btn_del)

    def mousePressEvent(self, event):
        self.clicked.emit(self.trip_id)
        super().mousePressEvent(event)

    def _on_del(self):
        self.delete_clicked.emit(self.trip_id)


class HistoryView(QWidget):
    back_requested = Signal()
    trip_selected = Signal(str) # trip_id
    delete_requested = Signal(str) # trip_id

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.create_particles()

    def create_particles(self):
        for _ in range(15):
            p = FloatingParticle(self, random.randint(0, 1000), random.randint(0, 800), random.randint(5, 15))
            p.lower()

    def init_ui(self):
        self.setStyleSheet("background: #0F172A; font-family: 'Segoe UI';")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 40, 50, 40)

        # Header
        header_layout = QHBoxLayout()
        btn_back = ScaleButton("⬅ Back", "#475569", "#334155")
        btn_back.setFixedSize(100, 40)
        btn_back.clicked.connect(self.back_requested.emit)
        
        title = QLabel("My Travel Log 🌍")
        title.setStyleSheet("font-size: 32px; font-weight: 800; color: white; border: none; background: transparent;")
        
        header_layout.addWidget(btn_back)
        header_layout.addSpacing(20)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(20)

        # Scroll Area for List
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QWidget#ScrollContent { background: transparent; }
        """)
        
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("ScrollContent")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(15)
        self.scroll_layout.addStretch() # Pushes items to top
        
        scroll.setWidget(self.scroll_content)
        main_layout.addWidget(scroll)

    def render_list(self, trips):
        # Clear existing
        for i in reversed(range(self.scroll_layout.count())): 
            widget = self.scroll_layout.itemAt(i).widget()
            if widget: widget.setParent(None)

        if not trips:
            lbl = QLabel("No trips found yet. Go plan one!")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #94A3B8; font-size: 18px; background: transparent;")
            self.scroll_layout.insertWidget(0, lbl)
            return

        # Add items
        for trip in trips:
            card = TripHistoryCard(
                trip_id=trip['id'],
                destination=trip.get('destination', 'Unknown'),
                date_str=trip.get('date', '')[:10],
                budget_str=str(trip.get('budget', '?'))
            )
            card.clicked.connect(self.trip_selected.emit)
            card.delete_clicked.connect(self.delete_requested.emit)
            
            # Insert at top (index 0) so newest is first, or append before stretch
            self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, card)