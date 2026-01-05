from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QSize

class HistoryItemWidget(QWidget):
    """Custom Row: Text + Delete Button (From your original code)"""
    delete_clicked = Signal(str)

    def __init__(self, text, trip_id):
        super().__init__()
        self.trip_id = trip_id
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.lbl_text = QLabel(text)
        self.lbl_text.setStyleSheet("font-size: 14px; color: #333;")
        
        self.btn_delete = QPushButton("🗑️")
        self.btn_delete.setFixedSize(30, 30)
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: #d32f2f; font-size: 16px; }
            QPushButton:hover { background: #ffebee; border-radius: 5px; }
        """)
        self.btn_delete.clicked.connect(lambda: self.delete_clicked.emit(self.trip_id))
        
        layout.addWidget(self.lbl_text)
        layout.addStretch()
        layout.addWidget(self.btn_delete)

class HistoryView(QWidget):
    back_clicked = Signal()
    trip_selected = Signal(str)   # Sends trip_id to presenter
    trip_deleted = Signal(str)    # Sends trip_id to presenter

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        # Header
        header_layout = QVBoxLayout()
        btn_back = QPushButton("🔙 Back to Menu")
        btn_back.setFixedSize(120, 30)
        btn_back.clicked.connect(self.back_clicked.emit)
        
        title = QLabel("My Trips 🌍")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1565c0; margin-top: 10px;")
        
        header_layout.addWidget(btn_back)
        header_layout.addWidget(title)
        layout.addLayout(header_layout)

        # List
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget { background: transparent; border: none; }
            QListWidget::item { 
                background: white; border-radius: 10px; border: 1px solid #ddd; 
                margin-bottom: 10px; 
            }
            QListWidget::item:hover { border: 1px solid #1565c0; background: #fdfdfd; }
        """)
        self.list_widget.itemClicked.connect(self._on_item_click)
        layout.addWidget(self.list_widget)

    def update_list(self, trips):
        self.list_widget.clear()
        
        if not trips:
            self.list_widget.addItem("No trips found yet.")
            return

        for trip in trips:
            # Handle Mongo IDs (which might be dicts or strings)
            trip_id = str(trip.get("id") or trip.get("_id"))
            dest = trip.get("destination", "Unknown")
            date = trip.get("date", "")[:10]
            budget = trip.get("budget", "?")

            display_text = f"✈️  {dest}  |  💰 Budget: {budget}  |  📅 {date}"

            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(0, 80))
            item.setData(Qt.UserRole, trip_id)

            # Create Custom Widget
            widget = HistoryItemWidget(display_text, trip_id)
            widget.delete_clicked.connect(self.trip_deleted.emit)

            self.list_widget.setItemWidget(item, widget)

    def _on_item_click(self, item):
        trip_id = item.data(Qt.UserRole)
        if trip_id:
            self.trip_selected.emit(trip_id)

    def confirm_delete(self):
        reply = QMessageBox.question(self, 'Delete Trip', 
                                     "Are you sure you want to delete this trip?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return reply == QMessageBox.Yes