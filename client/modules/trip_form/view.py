import random
from datetime import date
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, 
    QDateEdit, QComboBox, QPlainTextEdit, QMessageBox, 
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QColor

# Use your custom components
from components import FloatingParticle, ModernInput, ScaleButton

class TripFormView(QWidget):
    generate_requested = Signal(dict) # Sends form data to presenter
    back_requested = Signal()

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
        header = QLabel("Plan Your Next Adventure ✈️")
        header.setStyleSheet("font-size: 32px; font-weight: bold; color: white; margin-bottom: 20px;")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # --- Card Container ---
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
            }
        """)
        card.setFixedWidth(550)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30); shadow.setColor(QColor(0,0,0,80)); shadow.setOffset(0, 10)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(40, 40, 40, 40)

        # --- Inputs ---
        self.input_dest = ModernInput("Destination (e.g. Paris)", icon_char="📍")
        self.input_origin = ModernInput("Origin (e.g. New York)", icon_char="🏠")
        
        # Date Row
        date_layout = QHBoxLayout()
        self.date_start = self._create_date_edit()
        self.date_end = self._create_date_edit(offset_days=7)
        date_layout.addWidget(self._create_label("Start:", "black"))
        date_layout.addWidget(self.date_start)
        date_layout.addWidget(self._create_label("End:", "black"))
        date_layout.addWidget(self.date_end)

        # Budget Row
        budget_layout = QHBoxLayout()
        self.input_budget = ModernInput("Budget", icon_char="💰")
        self.input_budget.input_field.setFixedWidth(150)
        
        self.combo_currency = QComboBox()
        self.combo_currency.addItems(["USD", "EUR", "ILS", "GBP"])
        self.combo_currency.setFixedHeight(50)
        self.combo_currency.setStyleSheet("""
            QComboBox { border: 2px solid #E2E8F0; border-radius: 12px; padding: 5px; color: #1E293B; }
            QComboBox::drop-down { border: none; }
        """)
        
        budget_layout.addWidget(self.input_budget)
        budget_layout.addWidget(self.combo_currency)

        # Interests
        self.input_interests = QPlainTextEdit()
        self.input_interests.setPlaceholderText("Interests (Museums, Food, Hiking...)")
        self.input_interests.setFixedHeight(80)
        self.input_interests.setStyleSheet("""
            QPlainTextEdit {
                background: #F8FAFC; border: 2px solid #E2E8F0; border-radius: 12px;
                padding: 10px; font-size: 14px; color: #1E293B;
            }
            QPlainTextEdit:focus { border: 2px solid #3B82F6; background: white; }
        """)

        # Buttons
        self.btn_generate = ScaleButton("✨ Generate Trip", "#3B82F6", "#2563EB")
        self.btn_generate.clicked.connect(self.on_generate_click)

        self.btn_back = ScaleButton("Back to Dashboard", "#64748B", "#475569")
        self.btn_back.clicked.connect(self.back_requested.emit)

        # Assembly
        card_layout.addWidget(self._create_label("Where to?", "#334155"))
        card_layout.addWidget(self.input_dest)
        card_layout.addWidget(self.input_origin)
        card_layout.addSpacing(5)
        card_layout.addLayout(date_layout)
        card_layout.addSpacing(5)
        card_layout.addWidget(self._create_label("Budget", "#334155"))
        card_layout.addLayout(budget_layout)
        card_layout.addWidget(self.input_interests)
        card_layout.addSpacing(10)
        card_layout.addWidget(self.btn_generate)
        card_layout.addWidget(self.btn_back)

        main_layout.addWidget(card)

    def _create_date_edit(self, offset_days=0):
        de = QDateEdit()
        de.setCalendarPopup(True)
        de.setDate(QDate.currentDate().addDays(offset_days))
        de.setDisplayFormat("dd/MM/yyyy")
        de.setFixedHeight(45)
        de.setStyleSheet("""
            QDateEdit { background: #F8FAFC; border: 2px solid #E2E8F0; border-radius: 10px; color: #1E293B; padding-left: 10px;}
            QDateEdit::drop-down { border: none; }
        """)
        return de

    def _create_label(self, text, color):
        l = QLabel(text)
        l.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px; border: none; background: transparent;")
        return l

    def on_generate_click(self):
        data = {
            "destination": self.input_dest.text(),
            "origin": self.input_origin.text(),
            "budget": self.input_budget.text(),
            "currency": self.combo_currency.currentText(),
            "interests": self.input_interests.toPlainText(),
            "start_date": self.date_start.date().toPython(),
            "end_date": self.date_end.date().toPython()
        }
        self.generate_requested.emit(data)

    def show_loading(self, is_loading):
        if is_loading:
            self.btn_generate.setText("Generating... ⏳")
            self.btn_generate.setEnabled(False)
        else:
            self.btn_generate.setText("✨ Generate Trip")
            self.btn_generate.setEnabled(True)