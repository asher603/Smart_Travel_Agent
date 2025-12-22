import json
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                               QStackedWidget, QLineEdit, QSpinBox, QComboBox, 
                               QScrollArea, QMessageBox, QGridLayout, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QFont

try:
    from PySide6.QtCharts import QChart, QChartView, QPieSeries
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False

from client.components.custom_widgets import Card
from client.logic.workers import TripWorker

class DashboardScreen(QWidget):
    def __init__(self, switch_cb, api):
        super().__init__()
        self.switch_cb, self.api = switch_cb, api
        self.curr_user = None
        
        main = QVBoxLayout(self)
        main.setContentsMargins(20,20,20,20)
        
        # --- Header ---
        top = QHBoxLayout()
        self.lbl_welcome = QLabel("Hello!")
        self.lbl_welcome.setObjectName("Header")
        self.lbl_welcome.setStyleSheet("font-size: 28px; color: #1565c0;")
        
        btn_hist = QPushButton("📜 History")
        btn_hist.setObjectName("SecondaryBtn")
        btn_hist.clicked.connect(lambda: self.switch_cb("history", self.curr_user))
        
        btn_out = QPushButton("Logout")
        btn_out.setStyleSheet("""
            QPushButton { color: #e74c3c; border: 1px solid #e74c3c; border-radius: 8px; padding: 8px 16px; font-weight: bold; background: white; }
            QPushButton:hover { background-color: #fceceb; }
        """)
        btn_out.clicked.connect(lambda: self.switch_cb("login", None))
        
        top.addWidget(self.lbl_welcome)
        top.addStretch()
        top.addWidget(btn_hist)
        top.addSpacing(10)
        top.addWidget(btn_out)
        main.addLayout(top)

        self.stack = QStackedWidget()
        main.addWidget(self.stack)

        self.in_view = self.create_input()
        self.res_view = QWidget()
        self.setup_res()
        
        self.stack.addWidget(self.in_view)
        self.stack.addWidget(self.res_view)

    def create_input(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setAlignment(Qt.AlignCenter)
        
        # כרטיס ראשי רחב
        card = Card()
        card.setFixedWidth(800) # הרחבנו את הכרטיס
        
        # שימוש ב-Grid Layout לסידור מפלצתי
        grid = QGridLayout(card)
        grid.setContentsMargins(40,40,40,40)
        grid.setSpacing(20)
        
        # כותרת
        title = QLabel("Plan Your Ultimate Journey 🌍")
        title.setObjectName("Header")
        title.setAlignment(Qt.AlignCenter)
        grid.addWidget(title, 0, 0, 1, 2) # פורס על 2 עמודות

        # --- עמודה ימנית: פרטי מסלול ---
        lbl_route = QLabel("📍 Route Details")
        lbl_route.setStyleSheet("font-weight: bold; font-size: 16px; color: #555;")
        grid.addWidget(lbl_route, 1, 0)

        self.origin = QLineEdit()
        self.origin.setPlaceholderText("🛫 From (e.g. Tel Aviv)")
        grid.addWidget(self.origin, 2, 0)

        self.dest = QLineEdit()
        self.dest.setPlaceholderText("🛬 To (e.g. Tokyo)")
        grid.addWidget(self.dest, 3, 0)

        self.stops = QLineEdit()
        self.stops.setPlaceholderText("🛑 Stops (e.g. Dubai, Bangkok)")
        grid.addWidget(self.stops, 4, 0)

        # --- עמודה שמאלית: העדפות ---
        lbl_pref = QLabel("⚙️ Preferences")
        lbl_pref.setStyleSheet("font-weight: bold; font-size: 16px; color: #555;")
        grid.addWidget(lbl_pref, 1, 1)

        # שורת ימים ותקציב
        row_time = QHBoxLayout()
        self.days = QSpinBox()
        self.days.setRange(1, 30)
        self.days.setSuffix(" Days")
        self.days.setValue(5)
        self.days.setFixedHeight(45)
        
        self.interest = QComboBox()
        self.interest.addItems(["General 🌍", "History 🏛️", "Food 🍜", "Nature 🌲", "Extreme 🧗", "Shopping 🛍️"])
        self.interest.setFixedHeight(45)
        
        row_time.addWidget(self.days)
        row_time.addWidget(self.interest)
        grid.addLayout(row_time, 2, 1)

        # שורת כסף
        row_money = QHBoxLayout()
        self.currency = QComboBox()
        self.currency.addItems(["$ USD", "₪ ILS", "€ EUR", "£ GBP"])
        self.currency.setFixedHeight(45)
        self.currency.setFixedWidth(90)

        self.budget = QSpinBox()
        self.budget.setRange(100, 1000000)
        self.budget.setPrefix("Budget: ")
        self.budget.setValue(2000)
        self.budget.setFixedHeight(45)

        row_money.addWidget(self.currency)
        row_money.addWidget(self.budget)
        grid.addLayout(row_money, 3, 1)

        # כפתור ענק
        self.btn_go = QPushButton("🚀 Launch Planner")
        self.btn_go.setObjectName("PrimaryBtn")
        self.btn_go.setCursor(Qt.PointingHandCursor)
        self.btn_go.setFixedHeight(55)
        self.btn_go.setStyleSheet("""
            QPushButton { font-size: 18px; border-radius: 10px; background-color: #1565c0; color: white; border:none;}
            QPushButton:hover { background-color: #0d47a1; }
        """)
        self.btn_go.clicked.connect(self.go)
        
        grid.addWidget(self.btn_go, 5, 0, 1, 2) # כפתור למטה לרוחב הכל
        
        l.addWidget(card)
        return w

    def setup_res(self):
        l = QVBoxLayout(self.res_view)
        
        top = QHBoxLayout()
        btn_back = QPushButton("← Plan New Trip")
        btn_back.setObjectName("SecondaryBtn")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        top.addWidget(btn_back)
        top.addStretch()
        l.addLayout(top)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        self.content = QWidget()
        self.content.setObjectName("ScrollContents")
        self.content_l = QVBoxLayout(self.content)
        self.content_l.setSpacing(20)
        self.scroll.setWidget(self.content)
        l.addWidget(self.scroll)

    def go(self):
        if not self.dest.text() or not self.origin.text(): 
            QMessageBox.warning(self, "Missing Info", "Please fill in Origin and Destination!")
            return
            
        self.btn_go.setText("AI is analyzing routes... 📡")
        self.btn_go.setEnabled(False)
        
        # שליחת כל הנתונים החדשים
        self.worker = TripWorker(
            self.api, 
            self.curr_user, 
            self.dest.text(), 
            self.origin.text(),   # חדש
            self.stops.text(),    # חדש
            self.budget.value(), 
            self.currency.currentText(), # חדש
            self.interest.currentText(), 
            self.days.value()
        )
        self.worker.finished_signal.connect(self.show_res)
        self.worker.start()

    def show_res(self, data):
        self.btn_go.setText("🚀 Launch Planner")
        self.btn_go.setEnabled(True)
        
        for i in reversed(range(self.content_l.count())): 
            self.content_l.itemAt(i).widget().setParent(None)

        if "error" in data:
            QMessageBox.critical(self, "Error", str(data["error"]))
            return

        tp = data.get("trip_plan", {})
        if isinstance(tp, str): tp = json.loads(tp)

        # --- כרטיס סיכום מפלצתי ---
        sum_card = Card()
        sl = QVBoxLayout(sum_card)
        
        # כותרת עם מוצא ויעד
        trip_title = QLabel(f"✈️ {self.origin.text()} ➝ {self.dest.text()}")
        trip_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1565c0;")
        sl.addWidget(trip_title)
        
        # פרטים קטנים (מטבע, ימים)
        stops_str = f"via {self.stops.text()}" if self.stops.text() else "Direct Flight"
        details = QLabel(f"{self.days.value()} Days | {self.budget.value()} {self.currency.currentText()} | {stops_str}")
        details.setStyleSheet("color: #666; font-size: 14px; margin-bottom: 10px;")
        sl.addWidget(details)
        
        # סיכום טקסט
        desc = QLabel(tp.get("summary", "Your itinerary is ready."))
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 16px; line-height: 1.4;")
        sl.addWidget(desc)
        
        self.content_l.addWidget(sum_card)

        # גרף
        if "budget_breakdown" in tp and CHARTS_AVAILABLE:
            c = Card()
            c.setMinimumHeight(400)
            cl = QVBoxLayout(c)
            
            s = QPieSeries()
            for k,v in tp["budget_breakdown"].items(): 
                s.append(k,v)
            
            if s.slices(): 
                s.slices()[0].setExploded(True)
                s.slices()[0].setLabelVisible(True)
                
            chart = QChart()
            chart.addSeries(s)
            chart.setTitle(f"Budget Breakdown ({self.currency.currentText()})")
            chart.setTitleFont(QFont("Segoe UI", 16, QFont.Bold))
            chart.setAnimationOptions(QChart.SeriesAnimations)
            chart.setTheme(QChart.ChartThemeBlueCerulean)
            
            cv = QChartView(chart)
            cv.setRenderHint(QPainter.Antialiasing)
            cl.addWidget(cv)
            self.content_l.addWidget(c)

        # לו"ז יומי
        for d in tp.get("itinerary", []):
            c = Card()
            cl = QVBoxLayout(c)
            
            day_header = QLabel(f"Day {d.get('day')}: {d.get('title')}")
            day_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
            cl.addWidget(day_header)
            
            cl.addSpacing(10)
            
            for act in d.get("activities", []): 
                lbl = QLabel(f"• {act}")
                lbl.setWordWrap(True)
                lbl.setStyleSheet("font-size: 15px; margin-bottom: 4px;")
                cl.addWidget(lbl)
            self.content_l.addWidget(c)

        self.stack.setCurrentIndex(1)

    def set_user(self, u):
        self.curr_user = u
        self.lbl_welcome.setText(f"Welcome, {u} 👋")