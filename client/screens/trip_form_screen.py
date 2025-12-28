from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                               QLineEdit, QSpinBox, QPlainTextEdit, QMessageBox, QFrame)
from PySide6.QtCore import Qt

# --- הייבוא המעודכן מהקובץ החדש שיצרת ---
from client.screens.trip_screen import TripResultWindow

class TripFormScreen(QWidget):
    def __init__(self, switch_cb, api):
        super().__init__()
        self.switch_cb = switch_cb
        self.api = api
        self.curr_user = None
        self.windows = [] # רשימה לשמירת רפרנס לחלונות הפתוחים (כדי שלא ייסגרו לבד)
        
        self.setup_ui()

    def setup_ui(self):
        # סגנון מקומי לטופס
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI', Arial, sans-serif; }
            QLabel#Header { font-size: 26px; font-weight: 900; color: #1565c0; }
            QLabel#InputLabel { font-size: 13px; font-weight: 600; color: #546e7a; margin-top: 5px; }
            QLineEdit, QPlainTextEdit, QSpinBox { 
                background: white; border: 1px solid #cfd8dc; border-radius: 6px; padding: 8px; font-size: 14px;
            }
            QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus { border: 2px solid #2196f3; }
            QPushButton#ActionBtn {
                background-color: #1565c0; color: white; border: none; border-radius: 8px; padding: 12px; font-weight: bold; font-size: 15px;
            }
            QPushButton#ActionBtn:hover { background-color: #0d47a1; }
        """)

        main_l = QVBoxLayout(self)
        main_l.setAlignment(Qt.AlignCenter)
        
        # מסגרת הטופס
        card = QFrame()
        card.setStyleSheet("background: white; border-radius: 16px; border: 1px solid #e0e0e0;")
        card.setFixedWidth(500)
        l = QVBoxLayout(card)
        l.setSpacing(15)
        l.setContentsMargins(40, 40, 40, 40)
        
        # כותרת ויציאה
        top = QHBoxLayout()
        top.addWidget(QLabel("Plan Your Next Trip 🌍", objectName="Header"))
        btn_out = QPushButton("Logout")
        btn_out.setStyleSheet("color: red; border: none; font-weight: bold; background: transparent;")
        btn_out.setCursor(Qt.PointingHandCursor)
        btn_out.clicked.connect(lambda: self.switch_cb("login", None))
        top.addStretch()
        top.addWidget(btn_out)
        l.addLayout(top)
        
        l.addSpacing(10)
        
        # שדות קלט
        l.addWidget(QLabel("Destination:", objectName="InputLabel"))
        self.dest = QLineEdit()
        self.dest.setPlaceholderText("e.g. Paris, France")
        l.addWidget(self.dest)

        l.addWidget(QLabel("Origin:", objectName="InputLabel"))
        self.origin = QLineEdit()
        self.origin.setText("Tel Aviv")
        l.addWidget(self.origin)
        
        row = QHBoxLayout()
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("Days:", objectName="InputLabel"))
        self.days = QSpinBox(); self.days.setRange(1,60); self.days.setValue(5)
        v1.addWidget(self.days)
        
        v2 = QVBoxLayout()
        v2.addWidget(QLabel("Budget ($):", objectName="InputLabel"))
        self.budg = QSpinBox(); self.budg.setRange(100,100000); self.budg.setValue(2000)
        v2.addWidget(self.budg)
        row.addLayout(v1); row.addLayout(v2)
        l.addLayout(row)
        
        l.addWidget(QLabel("Interests:", objectName="InputLabel"))
        self.interest = QPlainTextEdit()
        self.interest.setPlaceholderText("e.g. Art, Food, Romantic...")
        self.interest.setFixedHeight(80)
        l.addWidget(self.interest)
        
        l.addSpacing(20)
        
        # כפתור השיגור
        btn_go = QPushButton("✨ Open Trip Window")
        btn_go.setObjectName("ActionBtn")
        btn_go.setCursor(Qt.PointingHandCursor)
        btn_go.clicked.connect(self.open_new_window)
        l.addWidget(btn_go)
        
        main_l.addWidget(card)

    def open_new_window(self):
        if not self.dest.text():
            QMessageBox.warning(self, "Error", "Destination is required!")
            return
            
        # איסוף הנתונים
        trip_data = {
            "dest": self.dest.text(),
            "origin": self.origin.text(),
            "days": self.days.value(),
            "budg": self.budg.value(),
            "interest": self.interest.toPlainText()
        }
        
        # יצירת מופע של החלון החדש מהקובץ הנפרד
        new_win = TripResultWindow(self.api, self.curr_user, trip_data)
        new_win.show()
        
        # שמירה ברשימה כדי שהחלון לא ייסגר מיד
        self.windows.append(new_win)

    def set_user(self, u):
        self.curr_user = u