from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
                               QLabel, QPushButton, QMessageBox)
from PySide6.QtCore import Qt

class HistoryScreen(QWidget):
    def __init__(self, switch_callback, api):
        super().__init__()
        self.switch_callback = switch_callback 
        self.api = api
        self.username = ""
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        header = QVBoxLayout()
        btn_back = QPushButton("🔙 Back to Menu")
        btn_back.setFixedSize(120, 30)
        btn_back.clicked.connect(lambda: self.switch_callback(1)) 
        header.addWidget(btn_back)
        
        title = QLabel("My Trips 🌍")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1565c0; margin-top: 10px;")
        header.addWidget(title)
        
        layout.addLayout(header)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget { background: transparent; border: none; }
            QListWidget::item { 
                background: white; border-radius: 10px; border: 1px solid #ddd; 
                padding: 15px; margin-bottom: 10px; 
            }
            QListWidget::item:hover { border: 1px solid #1565c0; background: #fdfdfd; }
        """)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_widget)

    def load_history(self, username):
        self.username = username
        self.list_widget.clear()
        
        # שלב 1: שליפת רשימה מקוצרת
        res = self.api.post("/get_history_summary", {"username": username})
        
        if not res or "trips" not in res or not res["trips"]:
            self.list_widget.addItem("No trips found yet.")
            return

        trips = res["trips"]
        for trip in trips:
            dest = trip.get("destination", "Unknown")
            date = trip.get("date", "")[:10]
            budget = trip.get("budget", "?")
            
            display_text = f"✈️  {dest}  |  💰 Budget: {budget}  |  📅 {date}"
            
            item = QListWidgetItem(display_text)
            # אנו שומרים רק את ה-ID בתוך הפריט
            item.setData(Qt.UserRole, trip["id"]) 
            self.list_widget.addItem(item)

    def on_item_clicked(self, item):
        trip_id = item.data(Qt.UserRole)
        if trip_id:
            # שלב 2: שליפת המידע המלא מהשרת לפני המעבר
            res = self.api.post("/get_full_trip", {"trip_id": trip_id})
            
            if res and "trip" in res:
                full_data = res["trip"]
                # מעבר למסך הטיול (3) עם המידע המלא לשחזור
                self.switch_callback(3, data=full_data, mode="load")
            else:
                QMessageBox.warning(self, "Error", "Could not load trip details.")