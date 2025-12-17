import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                               QWidget, QLabel, QLineEdit, QTextEdit, QMessageBox)
from PySide6.QtCore import QThread, Signal, Qt # הוספנו את המודולים האלו לניהול תהליכים
from api_service import APIService

# --- מחלקה חדשה: עובד רקע ---
class WorkerThread(QThread):
    # מגדירים "סיגנל" שישלח את הנתונים בחזרה לחלון הראשי כשהוא מסיים
    finished_signal = Signal(dict)

    def __init__(self, destination):
        super().__init__()
        self.destination = destination
        self.api = APIService()

    def run(self):
        # הפעולה הכבדה רצה כאן, ברקע, בלי לתקוע את החלון
        data = self.api.get_trip_plan(self.destination)
        self.finished_signal.emit(data)

# --- החלון הראשי ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Travel Agent")
        self.resize(600, 500)
        
        # --- עיצוב ו-Layout ---
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # כותרת
        self.title = QLabel("Plan Your Next Trip")
        self.title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(self.title)
        
        # שדה קלט
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter destination (e.g., London, Tokyo)...")
        self.input_field.setStyleSheet("padding: 8px; font-size: 14px;")
        layout.addWidget(self.input_field)

        # כפתור
        self.btn = QPushButton("Generate Itinerary")
        self.btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d7; 
                color: white; 
                padding: 10px; 
                font-size: 14px; 
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.btn.clicked.connect(self.on_click)
        layout.addWidget(self.btn)

        # אזור תוצאות
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        self.result_area.setStyleSheet("font-size: 14px; padding: 10px; border: 1px solid #ccc;")
        layout.addWidget(self.result_area)

        # הגדרת ה-Widget המרכזי
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def on_click(self):
        dest = self.input_field.text()
        
        if not dest:
            QMessageBox.warning(self, "Input Error", "Please enter a destination!")
            return

        # 1. חיווי למשתמש שהתהליך התחיל
        self.result_area.setText("🤖 AI Agent is thinking... please wait.\n(This might take a few seconds)")
        self.btn.setEnabled(False) # מכבים את הכפתור כדי שלא ילחצו פעמיים
        self.btn.setText("Generating...")

        # 2. יצירת ה-Thread והפעלתו
        self.worker = WorkerThread(dest)
        # מחברים את הסיגנל לפונקציה שתציג את התוצאה
        self.worker.finished_signal.connect(self.display_result)
        # מתחילים את העבודה ברקע
        self.worker.start()

    def display_result(self, data):
        """
        פונקציה זו נקראת אוטומטית כשה-Worker מסיים לעבוד
        """
        # החזרת הכפתור למצב רגיל
        self.btn.setEnabled(True)
        self.btn.setText("Generate Itinerary")

        # בדיקת שגיאות
        if "error" in data:
            self.result_area.setText(f"❌ Error: {data['error']}")
            return

        # --- הצגת התשובה ---
        # בשרת שבנינו, התשובה נמצאת בתוך מפתח 'trip_plan' שהוא טקסט אחד ארוך
        if 'trip_plan' in data:
            response_text = data['trip_plan']
            # מנקים קצת רווחים מיותרים אם יש
            formatted_text = f"✈️ TRIP PLAN FOR: {self.input_field.text().upper()}\n"
            formatted_text += "================================\n\n"
            formatted_text += response_text
            
            self.result_area.setText(formatted_text)
        else:
            # אם הפורמט לא צפוי, מציגים את מה שחזר כמו שהוא
            self.result_area.setText(str(data))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())