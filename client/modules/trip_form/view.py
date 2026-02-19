"""
Trip Form View - Polished Professional Design
"""
import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, 
    QComboBox, QPlainTextEdit, QMessageBox, QCalendarWidget,
    QGraphicsDropShadowEffect, QScrollArea, QPushButton, 
    QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QColor, QTextCharFormat, QBrush, QFont

from components.floating_particle import FloatingParticle
from components.modern_input import ModernInput
from components.ai_loading_view import AIAgentLoadingView


class InterestChip(QPushButton):
    """Elegant clickable interest chip"""
    def __init__(self, text, icon=""):
        super().__init__(f"{icon}  {text}" if icon else text)
        self.selected = False
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.clicked.connect(self.toggle)
        self.update_style()
    
    def toggle(self):
        self.selected = self.isChecked()
        self.update_style()
    
    def update_style(self):
        if self.selected:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #3B82F6, stop:1 #2563EB);
                    color: white;
                    border: none;
                    border-radius: 20px;
                    padding: 10px 16px;
                    font-size: 13px;
                    font-weight: 600;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: #F8FAFC;
                    color: #475569;
                    border: 1.5px solid #E2E8F0;
                    border-radius: 20px;
                    padding: 10px 16px;
                    font-size: 13px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    border-color: #3B82F6;
                    background: #EFF6FF;
                    color: #2563EB;
                }
            """)


class DateRangeCalendar(QFrame):
    """Polished date range calendar"""
    date_changed = Signal(QDate, QDate)
    
    def __init__(self):
        super().__init__()
        self.start_date = QDate.currentDate()
        self.end_date = QDate.currentDate().addDays(7)
        self.selecting_start = True
        
        self.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 20px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(35)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 10)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Title with gradient background
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                border-radius: 12px;
            }
        """)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("📅  Select Travel Dates")
        title.setStyleSheet("""
            QLabel {
                color: #1E293B;
                font-size: 17px;
                font-weight: 700;
                background: transparent;
            }
        """)
        title_layout.addWidget(title)
        layout.addWidget(title_frame)
        
        # Date boxes row
        dates_row = QHBoxLayout()
        dates_row.setSpacing(12)
        
        self.start_box = self._create_date_box("DEPARTURE", "🛫", True)
        dates_row.addWidget(self.start_box)
        
        arrow_lbl = QLabel("→")
        arrow_lbl.setStyleSheet("color: #94A3B8; font-size: 18px; font-weight: bold; background: transparent;")
        arrow_lbl.setAlignment(Qt.AlignCenter)
        arrow_lbl.setFixedWidth(30)
        dates_row.addWidget(arrow_lbl)
        
        self.end_box = self._create_date_box("RETURN", "🛬", False)
        dates_row.addWidget(self.end_box)
        
        layout.addLayout(dates_row)
        
        # Calendar widget
        self.calendar = QCalendarWidget()
        self.calendar.setMinimumDate(QDate.currentDate())
        self.calendar.setGridVisible(False)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.ShortDayNames)
        self.calendar.clicked.connect(self.on_date_clicked)
        self.calendar.setMinimumHeight(260)
        
        # Clean calendar styling - fixing all transparency issues
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: white;
                border: none;
            }
            
            /* Navigation bar */
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: white;
                border: none;
                border-bottom: 1px solid #E2E8F0;
                padding: 8px 4px;
            }
            
            /* Month/Year label button */
            QCalendarWidget QToolButton#qt_calendar_monthbutton,
            QCalendarWidget QToolButton#qt_calendar_yearbutton {
                color: #1E293B;
                font-size: 14px;
                font-weight: 700;
                background-color: transparent;
                border: none;
                padding: 6px 10px;
                border-radius: 6px;
            }
            QCalendarWidget QToolButton#qt_calendar_monthbutton:hover,
            QCalendarWidget QToolButton#qt_calendar_yearbutton:hover {
                background-color: #F1F5F9;
            }
            
            /* Arrow buttons */
            QCalendarWidget QToolButton#qt_calendar_prevmonth,
            QCalendarWidget QToolButton#qt_calendar_nextmonth {
                background-color: #F1F5F9;
                border: none;
                border-radius: 6px;
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
                qproperty-icon: none;
                color: #475569;
                font-size: 16px;
                font-weight: bold;
            }
            QCalendarWidget QToolButton#qt_calendar_prevmonth {
                qproperty-text: "◀";
            }
            QCalendarWidget QToolButton#qt_calendar_nextmonth {
                qproperty-text: "▶";
            }
            QCalendarWidget QToolButton#qt_calendar_prevmonth:hover,
            QCalendarWidget QToolButton#qt_calendar_nextmonth:hover {
                background-color: #E2E8F0;
                color: #1E293B;
            }
            
            /* Month dropdown menu */
            QCalendarWidget QMenu {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 4px;
            }
            QCalendarWidget QMenu::item {
                color: #1E293B;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QCalendarWidget QMenu::item:selected {
                background-color: #EFF6FF;
                color: #2563EB;
            }
            
            /* Year spinbox */
            QCalendarWidget QSpinBox {
                background-color: white;
                color: #1E293B;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 4px 8px;
                font-weight: 600;
                font-size: 14px;
                selection-background-color: #3B82F6;
                selection-color: white;
            }
            QCalendarWidget QSpinBox::up-button,
            QCalendarWidget QSpinBox::down-button {
                width: 18px;
                border: none;
                background-color: #F1F5F9;
            }
            QCalendarWidget QSpinBox::up-button:hover,
            QCalendarWidget QSpinBox::down-button:hover {
                background-color: #E2E8F0;
            }
            
            /* Calendar table view */
            QCalendarWidget QTableView {
                background-color: white;
                selection-background-color: transparent;
                outline: none;
                border: none;
            }
            
            /* All cells */
            QCalendarWidget QAbstractItemView:enabled {
                color: #1E293B;
                background-color: white;
                font-size: 13px;
                selection-background-color: transparent;
                selection-color: #1E293B;
            }
            
            /* Disabled dates (past dates, other months) */
            QCalendarWidget QAbstractItemView:disabled {
                color: #CBD5E1;
                background-color: white;
            }
            
            /* Header row (day names) */
            QCalendarWidget QHeaderView {
                background-color: white;
            }
            QCalendarWidget QHeaderView::section {
                background-color: white;
                color: #64748B;
                font-size: 11px;
                font-weight: 600;
                border: none;
                padding: 6px 0px;
            }
        """)
        
        layout.addWidget(self.calendar)
        
        # Duration display - matches project color scheme
        self.duration_label = QLabel()
        self.duration_label.setAlignment(Qt.AlignCenter)
        self.duration_label.setStyleSheet("""
            QLabel {
                color: #475569;
                font-size: 13px;
                font-weight: 600;
                padding: 10px 16px;
                background: #F1F5F9;
                border: 1.5px solid #E2E8F0;
                border-radius: 10px;
            }
        """)
        layout.addWidget(self.duration_label)
        
        self.update_display()
        self.highlight_range()
        self.set_selecting(True)
    
    def _create_date_box(self, label, icon, is_start):
        box = QFrame()
        box.setCursor(Qt.PointingHandCursor)
        box.setMinimumHeight(70)
        
        layout = QVBoxLayout(box)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)
        
        header = QLabel(f"{icon}  {label}")
        header.setStyleSheet("""
            QLabel {
                color: #64748B;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.5px;
                background-color: transparent;
                border: none;
            }
        """)
        layout.addWidget(header)
        
        date_lbl = QLabel()
        date_lbl.setStyleSheet("""
            QLabel {
                color: #1E293B;
                font-size: 13px;
                font-weight: 700;
                background-color: transparent;
                border: none;
            }
        """)
        layout.addWidget(date_lbl)
        
        if is_start:
            self.start_date_label = date_lbl
            box.mousePressEvent = lambda e: self.set_selecting(True)
        else:
            self.end_date_label = date_lbl
            box.mousePressEvent = lambda e: self.set_selecting(False)
        
        return box
    
    def set_selecting(self, is_start):
        self.selecting_start = is_start
        
        # Update box styles - active gets blue border
        if is_start:
            self.start_box.setStyleSheet("""
                QFrame {
                    background-color: #EFF6FF;
                    border-radius: 12px;
                    border: 2px solid #3B82F6;
                }
            """)
            self.end_box.setStyleSheet("""
                QFrame {
                    background-color: #F8FAFC;
                    border-radius: 12px;
                    border: 1px solid #E2E8F0;
                }
                QFrame:hover {
                    border-color: #CBD5E1;
                }
            """)
        else:
            self.start_box.setStyleSheet("""
                QFrame {
                    background-color: #F8FAFC;
                    border-radius: 12px;
                    border: 1px solid #E2E8F0;
                }
                QFrame:hover {
                    border-color: #CBD5E1;
                }
            """)
            self.end_box.setStyleSheet("""
                QFrame {
                    background-color: #EFF6FF;
                    border-radius: 12px;
                    border: 2px solid #3B82F6;
                }
            """)
    
    def on_date_clicked(self, date):
        if self.selecting_start:
            self.start_date = date
            if date > self.end_date:
                self.end_date = date.addDays(1)
            self.selecting_start = False
        else:
            if date >= self.start_date:
                self.end_date = date
            else:
                self.start_date = date
            self.selecting_start = True
        
        self.set_selecting(self.selecting_start)
        self.update_display()
        self.highlight_range()
        self.date_changed.emit(self.start_date, self.end_date)
    
    def update_display(self):
        self.start_date_label.setText(self.start_date.toString("MMM d, yyyy"))
        self.end_date_label.setText(self.end_date.toString("MMM d, yyyy"))
        
        days = self.start_date.daysTo(self.end_date)
        nights = max(0, days)
        self.duration_label.setText(
            f"✨  {nights} night{'s' if nights != 1 else ''}  •  {days + 1} day{'s' if days != 0 else ''}"
        )
    
    def highlight_range(self):
        # Clear all formats first
        clear_format = QTextCharFormat()
        clear_format.setBackground(QBrush(QColor("white")))
        clear_format.setForeground(QBrush(QColor("#1E293B")))
        
        # Reset a range of dates
        base = QDate.currentDate().addMonths(-1)
        for i in range(90):
            self.calendar.setDateTextFormat(base.addDays(i), clear_format)
        
        # Range format (middle days) - light blue background
        range_fmt = QTextCharFormat()
        range_fmt.setBackground(QBrush(QColor("#EFF6FF")))
        range_fmt.setForeground(QBrush(QColor("#1D4ED8")))
        
        # Endpoint format (start/end) - solid blue
        end_fmt = QTextCharFormat()
        end_fmt.setBackground(QBrush(QColor("#3B82F6")))
        end_fmt.setForeground(QBrush(QColor("#FFFFFF")))
        font = QFont()
        font.setBold(True)
        end_fmt.setFont(font)
        
        # Apply formats to range
        current = self.start_date
        while current <= self.end_date:
            if current == self.start_date or current == self.end_date:
                self.calendar.setDateTextFormat(current, end_fmt)
            else:
                self.calendar.setDateTextFormat(current, range_fmt)
            current = current.addDays(1)


class TripFormView(QWidget):
    """Polished Professional Trip Form"""
    generate_requested = Signal(dict)
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        self.resize(1280, 900)
        self.interest_chips = []
        self.init_ui()
        self.create_particles()
        
        # AI Loading screen
        self.loading_view = AIAgentLoadingView(self)

    def create_particles(self):
        for _ in range(8):
            size = random.randint(4, 10)
            x = random.randint(0, 1280)
            y = random.randint(0, 900)
            p = FloatingParticle(self, x, y, size)
            p.lower()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget { 
                background: #0F172A;
                font-family: 'Segoe UI', sans-serif; 
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ==================== HEADER ====================
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #3B82F6, stop:1 #2563EB);
            }
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        
        btn_back = QPushButton("←  Back")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.12);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 18px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.2);
            }
        """)
        btn_back.clicked.connect(self.back_requested.emit)
        header_layout.addWidget(btn_back)
        
        header_layout.addStretch()
        
        title = QLabel("Plan Your Trip")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: 700;
                background: transparent;
            }
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Empty space to balance header
        spacer = QWidget()
        spacer.setFixedWidth(80)
        spacer.setStyleSheet("background: transparent;")
        header_layout.addWidget(spacer)
        
        main_layout.addWidget(header)

        # ==================== CONTENT ====================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: rgba(255,255,255,0.03);
                width: 8px;
                border-radius: 4px;
                margin: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(99,102,241,0.4);
                border-radius: 4px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(99,102,241,0.6);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(32, 32, 32, 32)
        content_layout.setSpacing(24)

        # ========== LEFT COLUMN ==========
        left_col = QVBoxLayout()
        left_col.setSpacing(20)
        
        # Location Card
        loc_card = self._card()
        loc_layout = QVBoxLayout(loc_card)
        loc_layout.setContentsMargins(28, 16, 28, 16)
        loc_layout.setSpacing(6)
        
        loc_title = QLabel("📍 Location")
        loc_title.setStyleSheet("color: #1E293B; font-size: 17px; font-weight: 700;")
        loc_layout.addWidget(loc_title)
        
        # Destination
        dest_lbl = QLabel("Where to?")
        dest_lbl.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600;")
        loc_layout.addWidget(dest_lbl)
        self.input_dest = ModernInput("Enter destination city", icon_char="✈️")
        loc_layout.addWidget(self.input_dest)
        
        # Origin
        origin_lbl = QLabel("From")
        origin_lbl.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600;")
        loc_layout.addWidget(origin_lbl)
        self.input_origin = ModernInput("Your departure city", icon_char="🏠")
        loc_layout.addWidget(self.input_origin)
        
        left_col.addWidget(loc_card)
        
        # Budget Card
        budget_card = self._card()
        budget_layout = QVBoxLayout(budget_card)
        budget_layout.setContentsMargins(28, 24, 28, 28)
        budget_layout.setSpacing(16)
        
        budget_title = QLabel("💰 Budget")
        budget_title.setStyleSheet("color: #1E293B; font-size: 17px; font-weight: 700;")
        budget_layout.addWidget(budget_title)
        
        budget_row = QHBoxLayout()
        budget_row.setSpacing(12)
        
        #self.input_budget = ModernInput("Amount", icon_char="")
        self.input_budget = ModernInput("", icon_char="")
        budget_row.addWidget(self.input_budget, 2)
        
        self.combo_currency = self._combo(["USD", "EUR", "ILS", "GBP", "JPY"])
        self.combo_currency.setFixedWidth(100)
        budget_row.addWidget(self.combo_currency, 1)
        
        budget_layout.addLayout(budget_row)
        left_col.addWidget(budget_card)
        
        # Traveler Card (Gender)
        traveler_card = self._card()
        traveler_layout = QVBoxLayout(traveler_card)
        traveler_layout.setContentsMargins(28, 20, 28, 20)
        traveler_layout.setSpacing(14)

        # Gender label
        gender_lbl = QLabel("👤 Travelers Gender")
        gender_lbl.setStyleSheet("color: #1E293B; font-size: 15px; font-weight: 700;")
        traveler_layout.addWidget(gender_lbl)

        # Gender combo
        gender_row = QHBoxLayout()
        self.combo_gender = self._combo(["Male", "Female", "Both"])
        gender_row.addWidget(self.combo_gender)
        gender_row.addStretch()
        traveler_layout.addLayout(gender_row)

        left_col.addWidget(traveler_card)
        left_col.addStretch()
        
        content_layout.addLayout(left_col, 1)

        # ========== CENTER - CALENDAR ==========
        center_col = QVBoxLayout()
        center_col.setSpacing(0)
        
        self.date_picker = DateRangeCalendar()
        self.date_picker.setMinimumWidth(400)
        self.date_picker.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        center_col.addWidget(self.date_picker)
        center_col.addStretch()
        
        content_layout.addLayout(center_col, 1)

        # ========== RIGHT - INTERESTS ==========
        right_col = QVBoxLayout()
        right_col.setSpacing(20)
        
        interests_card = self._card()
        interests_layout = QVBoxLayout(interests_card)
        interests_layout.setContentsMargins(28, 24, 28, 28)
        interests_layout.setSpacing(16)
        
        int_title = QLabel("🎯 Your Interests")
        int_title.setStyleSheet("color: #1E293B; font-size: 17px; font-weight: 700;")
        interests_layout.addWidget(int_title)
        
        int_hint = QLabel("Select what excites you")
        int_hint.setStyleSheet("color: #94A3B8; font-size: 12px;")
        interests_layout.addWidget(int_hint)
        
        # Chips in flow layout simulation
        interests = [
            ("🏛️", "Museums"), ("🍜", "Food"), ("🏔️", "Adventure"),
            ("🏖️", "Beach"), ("🛍️", "Shopping"), ("🎉", "Nightlife"),
            ("📸", "Photo"), ("🏛️", "History"), ("🌿", "Nature"),
            ("🎨", "Art"), ("⚽", "Sports"), ("💆", "Wellness"),
        ]
        
        # Row 1
        row1 = QHBoxLayout()
        row1.setSpacing(8)
        for i in range(4):
            chip = InterestChip(interests[i][1], interests[i][0])
            self.interest_chips.append(chip)
            row1.addWidget(chip)
        row1.addStretch()
        interests_layout.addLayout(row1)
        
        # Row 2
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        for i in range(4, 8):
            chip = InterestChip(interests[i][1], interests[i][0])
            self.interest_chips.append(chip)
            row2.addWidget(chip)
        row2.addStretch()
        interests_layout.addLayout(row2)
        
        # Row 3
        row3 = QHBoxLayout()
        row3.setSpacing(8)
        for i in range(8, 12):
            chip = InterestChip(interests[i][1], interests[i][0])
            self.interest_chips.append(chip)
            row3.addWidget(chip)
        row3.addStretch()
        interests_layout.addLayout(row3)
        
        # Other interests
        other_lbl = QLabel("Other:")
        other_lbl.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600; margin-top: 8px;")
        interests_layout.addWidget(other_lbl)
        
        self.input_interests = QPlainTextEdit()
        self.input_interests.setPlaceholderText("Any other interests...")
        self.input_interests.setFixedHeight(50)
        self.input_interests.setStyleSheet("""
            QPlainTextEdit {
                background: #F8FAFC;
                border: 1.5px solid #E2E8F0;
                border-radius: 10px;
                padding: 10px 12px;
                font-size: 13px;
                color: #1E293B;
            }
            QPlainTextEdit:focus {
                border-color: #3B82F6;
            }
        """)
        interests_layout.addWidget(self.input_interests)
        
        right_col.addWidget(interests_card)
        
        # Generate Button row - AI model combo + button side by side
        generate_row = QHBoxLayout()
        generate_row.setSpacing(10)

        self.combo_model = self._combo(["Gemini", "Groq", "Ollama"])
        self.combo_model.setFixedWidth(110)
        self.combo_model.setFixedHeight(52)
        generate_row.addWidget(self.combo_model)

        self.btn_generate = QPushButton("Generate Trip  →")
        self.btn_generate.setCursor(Qt.PointingHandCursor)
        self.btn_generate.setFixedHeight(52)
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #3B82F6, stop:1 #2563EB);
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 15px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #2563EB, stop:1 #1D4ED8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #1D4ED8, stop:1 #1E40AF);
            }
        """)
        self.btn_generate.clicked.connect(self.on_generate_click)

        btn_shadow = QGraphicsDropShadowEffect()
        btn_shadow.setBlurRadius(20)
        btn_shadow.setColor(QColor(59, 130, 246, 80))
        btn_shadow.setOffset(0, 6)
        self.btn_generate.setGraphicsEffect(btn_shadow)

        generate_row.addWidget(self.btn_generate)
        right_col.addLayout(generate_row)
        right_col.addStretch()
        
        content_layout.addLayout(right_col, 1)
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _card(self):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 18px;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 6)
        card.setGraphicsEffect(shadow)
        return card

    def _combo(self, items):
        combo = QComboBox()
        combo.addItems(items)
        combo.setCursor(Qt.PointingHandCursor)
        combo.setFixedHeight(44)
        combo.setStyleSheet("""
            QComboBox {
                background: #F8FAFC;
                border: 1.5px solid #E2E8F0;
                border-radius: 10px;
                padding: 8px 14px;
                font-size: 13px;
                font-weight: 600;
                color: #1E293B;
            }
            QComboBox:hover {
                border-color: #3B82F6;
            }
            QComboBox::drop-down {
                width: 24px;
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #64748B;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                selection-background-color: #EFF6FF;
                selection-color: #2563EB;
                color: #1E293B;
                padding: 4px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                min-height: 32px;
                padding: 6px 12px;
                border-radius: 4px;
            }
        """)
        return combo

    def on_generate_click(self):
        selected = [chip.text().strip() for chip in self.interest_chips if chip.selected]
        other = self.input_interests.toPlainText().strip()
        if other:
            selected.append(other)
        
        data = {
            "destination": self.input_dest.text(),
            "origin": self.input_origin.text(),
            "budget": self.input_budget.text(),
            "currency": self.combo_currency.currentText(),
            "interests": ", ".join(selected),
            "start_date": self.date_picker.start_date.toString("yyyy-MM-dd"),
            "end_date": self.date_picker.end_date.toString("yyyy-MM-dd"),
            "model": self.combo_model.currentText().lower(),
            "gender": self.combo_gender.currentText().lower()
        }
        self.generate_requested.emit(data)

    def show_loading(self, is_loading):
        if is_loading:
            # Show AI loading view
            self.loading_view.show_loading(
                title="AI Agent Working",
                subtitle="Creating your perfect trip..."
            )
            
            # Also disable the button
            self.btn_generate.setText("Creating trip...")
            self.btn_generate.setEnabled(False)
            self.btn_generate.setStyleSheet("""
                QPushButton {
                    background: #94A3B8;
                    color: white;
                    border: none;
                    border-radius: 14px;
                    font-size: 15px;
                    font-weight: 700;
                }
            """)
        else:
            # Hide AI loading view
            self.loading_view.hide_loading()
            
            self.btn_generate.setText("Generate Trip  →")
            self.btn_generate.setEnabled(True)
            self.btn_generate.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #3B82F6, stop:1 #2563EB);
                    color: white;
                    border: none;
                    border-radius: 14px;
                    font-size: 15px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #2563EB, stop:1 #1D4ED8);
                }
            """)
    
    def resizeEvent(self, event):
        """Handle resize to keep loading view fullscreen"""
        super().resizeEvent(event)
        if hasattr(self, 'loading_view'):
            self.loading_view.resize(self.size())

    def show_message(self, title, message):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStyleSheet("""
            QMessageBox { background: #1E293B; }
            QMessageBox QLabel { color: white; font-size: 14px; }
            QMessageBox QPushButton {
                background: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: 600;
            }
            QMessageBox QPushButton:hover {
                background: #2563EB;
            }
        """)
        msg.exec()