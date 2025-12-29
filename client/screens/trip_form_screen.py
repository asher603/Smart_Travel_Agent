from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QComboBox, QPlainTextEdit, 
    QMessageBox, QFrame, QDateEdit, QFormLayout
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QIcon

class TripFormScreen(QWidget):
    # סיגנל שמודיע למיין שהטיול נוצר בהצלחה
    trip_generated = Signal(dict)

    def __init__(self, api_service):
        super().__init__()
        self.api_service = api_service
        self.username = "Guest"  # ייקבע מחדש על ידי ה-MainApp
        # משתנה קריטי: שומר את מה שהמשתמש הזין כדי להעביר למסך הבא
        self.current_request_data = {} 
        self.init_ui()

    def init_ui(self):
        # לייאוט ראשי
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setAlignment(Qt.AlignCenter)

        # --- כותרת ראשית ---
        header = QLabel("Plan Your Next Adventure ✈️")
        header.setObjectName("Header")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # --- הכרטיס הלבן (The Card) ---
        card = QFrame()
        card.setObjectName("Card")
        card.setFixedWidth(500)
        
        # צללית לכרטיס
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(30, 30, 30, 30)

        # --- טופס הזנת פרטים ---
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignLeft)

        # יעד
        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("E.g., Paris, Tokyo, New York")
        form_layout.addRow("Destination:", self.dest_input)

        # מוצא
        self.origin_input = QLineEdit()
        self.origin_input.setPlaceholderText("E.g., Tel Aviv")
        form_layout.addRow("Origin:", self.origin_input)

        # --- תאריכים ---
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(7))
        self.start_date.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Start Date:", self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addDays(12))
        self.end_date.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("End Date:", self.end_date)

        # תקציב ומטבע
        budget_layout = QHBoxLayout()
        self.budget_input = QLineEdit()
        self.budget_input.setPlaceholderText("2000")
        self.currency_input = QComboBox()
        self.currency_input.addItems(["USD", "EUR", "ILS", "GBP"])
        budget_layout.addWidget(self.budget_input)
        budget_layout.addWidget(self.currency_input)
        form_layout.addRow("Budget:", budget_layout)

        # תחומי עניין
        self.interest_input = QPlainTextEdit()
        self.interest_input.setPlaceholderText("I like museums, food, hiking...")
        self.interest_input.setFixedHeight(80)
        form_layout.addRow("Interests:", self.interest_input)

        card_layout.addLayout(form_layout)

        # כפתור פעולה
        self.generate_btn = QPushButton("✨ Generate My Trip")
        self.generate_btn.setObjectName("PrimaryBtn")
        self.generate_btn.setCursor(Qt.PointingHandCursor)
        self.generate_btn.clicked.connect(self.handle_generate)
        card_layout.addWidget(self.generate_btn)

        main_layout.addWidget(card)

    def handle_generate(self):
        dest = self.dest_input.text().strip()
        origin = self.origin_input.text().strip()
        budget = self.budget_input.text().strip()
        interest = self.interest_input.toPlainText().strip()
        
        # חישוב משך הטיול
        start = self.start_date.date()
        end = self.end_date.date()
        duration = start.daysTo(end)

        # ולידציות
        if not dest or not budget:
            QMessageBox.warning(self, "Missing Data", "Please fill in Destination and Budget.")
            return

        if duration < 1:
            QMessageBox.warning(self, "Invalid Dates", "End date must be after start date!")
            return

        # הכנת הנתונים לסנכרון עם TripRequest בשרת
        trip_data = {
            "username": self.username, # <--- התיקון הקריטי: שם המשתמש נשלח לשרת
            "destination": dest,
            "origin": origin,
            "budget": int(budget) if budget.isdigit() else 0,
            "currency": self.currency_input.currentText(),
            "interest": interest,
            "duration": duration,
            "start_date": start.toString("yyyy-MM-dd"),
            "end_date": end.toString("yyyy-MM-dd")
        }
        
        # שמירת הנתונים בצד
        self.current_request_data = trip_data 
        
        # שינוי כפתור לחיווי טעינה
        self.generate_btn.setText("Generating... ⏳")
        self.generate_btn.setEnabled(False)

        # שליחה לשרת (ה-API Service כבר יודע לטפל בזה)
        self.api_service.generate_trip(trip_data, self.on_success, self.on_error)

    def on_success(self, response):
        self.generate_btn.setText("✨ Generate My Trip")
        self.generate_btn.setEnabled(True)
        
        # איחוד המידע
        full_data = self.current_request_data.copy()
        full_data.update(response)
        
        self.trip_generated.emit(full_data)

    def on_error(self, error_msg):
        self.generate_btn.setText("✨ Generate My Trip")
        self.generate_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Failed to generate trip:\n{error_msg}")