from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
                               QLabel, QPushButton, QMessageBox, QHBoxLayout)
from PySide6.QtCore import Qt, Signal

class HistoryItemWidget(QWidget):
    """וידג'ט מותאם אישית לשורה בהיסטוריה: טקסט + כפתור מחיקה"""
    delete_clicked = Signal(str) # משדר את ה-ID למחיקה

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
        self.btn_delete.clicked.connect(self.on_delete)
        
        layout.addWidget(self.lbl_text)
        layout.addStretch()
        layout.addWidget(self.btn_delete)

    def on_delete(self):
        self.delete_clicked.emit(self.trip_id)


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
                margin-bottom: 10px; 
            }
            QListWidget::item:hover { border: 1px solid #1565c0; background: #fdfdfd; }
        """)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_widget)

    def load_history(self, username):
        self.username = username
        self.list_widget.clear()
        
        res = self.api.post("/get_history_summary", {"username": username})
        
        if not res or "trips" not in res or not res["trips"]:
            self.list_widget.addItem("No trips found yet.")
            return

        trips = res["trips"]
        for trip in trips:
            dest = trip.get("destination", "Unknown")
            date = trip.get("date", "")[:10]
            budget = trip.get("budget", "?")
            trip_id = trip["id"]
            
            display_text = f"✈️  {dest}  |  💰 Budget: {budget}  |  📅 {date}"
            
            # יצירת פריט רשימה
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(0, 80)) # גובה השורה
            
            # יצירת הוידג'ט המותאם
            widget = HistoryItemWidget(display_text, trip_id)
            widget.delete_clicked.connect(self.delete_trip)
            
            self.list_widget.setItemWidget(item, widget)
            item.setData(Qt.UserRole, trip_id) # שומרים את ה-ID גם בפריט עצמו

    def on_item_clicked(self, item):
        trip_id = item.data(Qt.UserRole)
        # אם לחצו על הכפתור מחיקה, האירוע מטופל שם. כאן זה לחיצה על כל השורה.
        if trip_id:
            res = self.api.post("/get_full_trip", {"trip_id": trip_id})
            if res and "trip" in res:
                self.switch_callback(3, data=res["trip"], mode="load")
            else:
                QMessageBox.warning(self, "Error", "Could not load trip details.")

    def delete_trip(self, trip_id):
        reply = QMessageBox.question(self, 'Delete Trip', 
                                     "Are you sure you want to delete this trip?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            res = self.api.post("/delete_trip", {"trip_id": trip_id})
            if res.get("status") == "success":
                self.load_history(self.username) # רענון הרשימה
            else:
                QMessageBox.warning(self, "Error", "Failed to delete trip.")

from PySide6.QtCore import QSize