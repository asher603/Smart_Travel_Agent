import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QPushButton, QFrame, 
    QMessageBox, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor
from components import FloatingParticle, ScaleButton

class HistoryItemWidget(QWidget):
    """Custom Row Widget: Text + Delete Button"""
    delete_clicked = Signal(str) # Emits trip_id

    def __init__(self, text, trip_id):
        super().__init__()
        self.trip_id = trip_id
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.lbl_text = QLabel(text)
        self.lbl_text.setStyleSheet("font-size: 15px; color: #334155; font-weight: 500;")
        
        self.btn_delete = QPushButton("🗑️")
        self.btn_delete.setFixedSize(35, 35)
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.setStyleSheet("""
            QPushButton { background: #FEE2E2; border: none; border-radius: 8px; color: #DC2626; font-size: 16px; }
            QPushButton:hover { background: #FECACA; }
        """)
        self.btn_delete.clicked.connect(self.on_delete)
        
        layout.addWidget(self.lbl_text)
        layout.addStretch()
        layout.addWidget(self.btn_delete)

    def on_delete(self):
        self.delete_clicked.emit(self.trip_id)


class HistoryView(QWidget):
    back_signal = Signal()
    trip_clicked_signal = Signal(str) # Emits trip_id to presenter
    delete_trip_signal = Signal(str)  # Emits trip_id to presenter

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.create_particles()

    def create_particles(self):
        for _ in range(20):
            size = random.randint(5, 15)
            x = random.randint(0, 1000)
            y = random.randint(0, 800)
            p = FloatingParticle(self, x, y, size)
            p.lower()

    def init_ui(self):
        self.setStyleSheet("background: #0F172A; font-family: 'Segoe UI'; color: white;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(50, 50, 50, 50)

        # --- Header ---
        header = QLabel("My Trips 🌍")
        header.setStyleSheet("font-size: 32px; font-weight: bold; color: white; margin-bottom: 20px; background: transparent;")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # --- Card Container ---
        card = QFrame()
        card.setStyleSheet("background-color: white; border-radius: 20px;")
        card.setFixedWidth(700) # Wider for the list
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40); shadow.setColor(QColor(0,0,0,80)); shadow.setOffset(0, 10)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(40, 40, 40, 40)

        # --- List Widget ---
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget { background: transparent; border: none; outline: none; }
            QListWidget::item { 
                background: #F8FAFC; border-radius: 12px; border: 1px solid #E2E8F0; 
                margin-bottom: 10px; 
            }
            QListWidget::item:hover { border: 1px solid #3B82F6; background: #EFF6FF; }
            QListWidget::item:selected { background: #EFF6FF; border: 1px solid #3B82F6; }
        """)
        self.list_widget.itemClicked.connect(self.on_row_clicked)
        card_layout.addWidget(self.list_widget)

        # --- Back Button ---
        self.btn_back = ScaleButton("Back to Dashboard", "#64748B", "#475569")
        self.btn_back.clicked.connect(self.back_signal.emit)
        card_layout.addWidget(self.btn_back)

        main_layout.addWidget(card)

    def update_list(self, trips):
        self.list_widget.clear()
        
        if not trips:
            item = QListWidgetItem("No trips found yet. Go plan one!")
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(Qt.NoItemFlags) # Not clickable
            self.list_widget.addItem(item)
            return

        for trip in trips:
            dest = trip.get("destination", "Unknown")
            date = trip.get("date", "")[:10]
            budget = trip.get("budget", "?")
            trip_id = trip.get("id") or trip.get("_id") # Handle Mongo ID variations
            
            display_text = f"✈️  {dest}   |   💰 {budget}   |   📅 {date}"
            
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(0, 80))
            item.setData(Qt.UserRole, str(trip_id)) # Store ID
            
            # Create Custom Row Widget
            row_widget = HistoryItemWidget(display_text, str(trip_id))
            row_widget.delete_clicked.connect(self.delete_trip_signal.emit)
            
            self.list_widget.setItemWidget(item, row_widget)

    def on_row_clicked(self, item):
        trip_id = item.data(Qt.UserRole)
        if trip_id:
            self.trip_clicked_signal.emit(trip_id)

    def show_message(self, title, msg):
        QMessageBox.information(self, title, msg)
        
    def confirm_delete(self):
        reply = QMessageBox.question(self, 'Delete Trip', 
            "Are you sure you want to delete this trip?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return reply == QMessageBox.Yes