import json
import base64
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QScrollArea, QFrame, QSplitter, 
    QListWidget, QListWidgetItem, QDialog, QSizePolicy, QLayout, 
    QDateEdit, QStackedWidget,
    QMessageBox, QFileDialog # <--- CRITICAL IMPORTS ADDED HERE
)
from PySide6.QtCore import Qt, QThread, Signal, QByteArray, QTimer, QSize, QDate
from PySide6.QtGui import QPixmap, QImage, QCursor, QPainter, QPainterPath
from client.components.custom_widgets import Card
from client.pdf_generator import generate_trip_pdf 

# --- Try Importing Charts ---
try:
    from client.components.charts import BudgetPieChart
except ImportError:
    BudgetPieChart = None

# --- Helper Widget: Clickable Image ---
class ClickableImage(QLabel):
    clicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

# --- Workers ---
class ImageWorker(QThread):
    finished_signal = Signal(str) 
    def __init__(self, api, destination, interest):
        super().__init__()
        self.api = api; self.destination = destination; self.interest = interest
    def run(self):
        try:
            response = self.api.post("/generate_image", {"destination": self.destination, "interest": self.interest})
            self.finished_signal.emit(response.get("image_base64") if response else None)
        except: self.finished_signal.emit(None)

class ChatWorker(QThread):
    finished_signal = Signal(str)
    def __init__(self, api, question, context):
        super().__init__()
        self.api = api; self.question = question; self.context = context
    def run(self):
        try:
            response = self.api.post("/ask_question", {"question": self.question, "context": self.context})
            self.finished_signal.emit(response.get("answer", "No response"))
        except: self.finished_signal.emit("Error connecting")

class StateSaverWorker(QThread):
    def __init__(self, api, trip_id, history):
        super().__init__()
        self.api = api; self.trip_id = trip_id; self.history = history
    def run(self):
        self.api.post("/update_trip_state", {"trip_id": self.trip_id, "chat_history": self.history})

class WeatherWorker(QThread):
    finished_signal = Signal(dict)
    def __init__(self, api, destination):
        super().__init__()
        self.api = api
        self.destination = destination
    def run(self):
        # Ensure your api_service has get_weather
        if hasattr(self.api, 'get_weather'):
            result = self.api.get_weather(self.destination)
            self.finished_signal.emit(result)
        else:
            self.finished_signal.emit({"error": "API missing get_weather"})

class FlightWorker(QThread):
    finished_signal = Signal(list)
    def __init__(self, api, origin, dest, date):
        super().__init__()
        self.api = api; self.origin = origin; self.dest = dest; self.date = date
    def run(self):
        resp = self.api.post("/get_flights", {"from": self.origin, "to": self.dest, "date": self.date})
        if resp and "flights" in resp:
            self.finished_signal.emit(resp["flights"])
        else:
            self.finished_signal.emit([])

class BudgetWorker(QThread):
    finished_signal = Signal(dict)
    def __init__(self, api, budget):
        super().__init__()
        self.api = api; self.budget = budget
    def run(self):
        resp = self.api.post("/analyze_budget", {"budget": self.budget})
        self.finished_signal.emit(resp.get("breakdown", {}))

class ImagePopup(QDialog):
    def __init__(self, pixmap, title="Trip Vibe"):
        super().__init__()
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(900, 700)
        layout = QVBoxLayout(self)
        
        lbl_img = QLabel()
        lbl_img.setPixmap(pixmap.scaled(880, 680, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        lbl_img.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_img)
        
        btn_close = QPushButton("Close")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

class TripScreen(QWidget):
    def __init__(self, switch_screen_callback, api):
        super().__init__()
        self.switch_screen = switch_screen_callback
        self.api = api
        self.trip_id = None
        self.username = ""
        self.trip_counter = 0
        
        # Mappings
        self.trip_widgets_map = {}
        self.image_placeholders = {} 
        self.weather_labels = {} 
        
        self.chat_history_state = [] 
        self.active_workers = []
        self.is_loading_mode = False
        
        self.current_active_ver_id = None 

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        
        # --- Top Bar ---
        top = QHBoxLayout()
        top.setContentsMargins(10, 10, 10, 0)
        
        btn_back = QPushButton("🔙 Back to Menu")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(self.go_back)
        top.addWidget(btn_back)
        
        top.addStretch() # דוחף את הכפתורים לצדדים
        
        # --- כפתור PDF החדש ---
        self.btn_pdf = QPushButton("📄 Download PDF") # <--- NEW
        self.btn_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_pdf.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 6px 12px; border-radius: 5px;")
        self.btn_pdf.clicked.connect(self.save_pdf)
        self.btn_pdf.setVisible(False) # מוסתר עד שיש טיול
        top.addWidget(self.btn_pdf)
        # ---------------------

        main_layout.addLayout(top)

        # --- Splitter Content ---
        splitter = QSplitter(Qt.Horizontal)
        
        # TOC
        self.toc_widget = QWidget(); self.toc_widget.setFixedWidth(200)
        tl = QVBoxLayout(self.toc_widget)
        tl.addWidget(QLabel("📅 Versions")); self.trip_list = QListWidget()
        self.trip_list.itemClicked.connect(self.scroll_to_item)
        tl.addWidget(self.trip_list)
        
        # Feed Area
        self.scroll_area = QScrollArea(); self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.feed_cont = QWidget()
        self.feed_cont.setStyleSheet("background: transparent;")
        self.feed_layout = QVBoxLayout(self.feed_cont)
        self.feed_layout.setSpacing(20)
        self.feed_layout.setContentsMargins(20, 0, 20, 20)
        self.feed_layout.addStretch()
        
        self.scroll_area.setWidget(self.feed_cont)
        
        splitter.addWidget(self.toc_widget); splitter.addWidget(self.scroll_area)
        main_layout.addWidget(splitter)
        
        # --- Chat Box ---
        chat_box = QHBoxLayout(); chat_box.setContentsMargins(10, 10, 10, 10)
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask a question or request a change...")
        self.chat_input.returnPressed.connect(self.on_send)
        
        self.mode_combo = QComboBox(); self.mode_combo.addItems(["❓ Question", "🛠️ Fix / New Trip"])
        
        btn_send = QPushButton("➤")
        btn_send.setCursor(Qt.PointingHandCursor)
        btn_send.setFixedSize(40, 40)
        btn_send.setStyleSheet("""
            QPushButton { 
                background-color: #1565c0; 
                color: white; 
                border-radius: 20px; 
                font-size: 18px; 
                font-weight: bold;
                padding-bottom: 3px;
            }
            QPushButton:hover { background-color: #0d47a1; }
        """)
        btn_send.clicked.connect(self.on_send)
        
        chat_box.addWidget(self.mode_combo); chat_box.addWidget(self.chat_input); chat_box.addWidget(btn_send)
        main_layout.addLayout(chat_box)

    def start_worker(self, worker):
        self.active_workers.append(worker)
        worker.finished.connect(lambda: self.cleanup_worker(worker))
        worker.start()

    def cleanup_worker(self, worker):
        if worker in self.active_workers: self.active_workers.remove(worker)
        worker.deleteLater()

    def go_back(self):
        if not self.is_loading_mode: self.save_state_to_server()
        self.switch_screen(1)

    def reset_ui(self):
        self.trip_list.clear(); self.chat_history_state = []
        self.trip_counter = 0
        self.trip_widgets_map = {}
        self.image_placeholders = {}
        self.weather_labels = {}
        self.active_workers.clear()
        
        while self.feed_layout.count() > 1:
            i = self.feed_layout.takeAt(0)
            if i.widget(): i.widget().deleteLater()
            elif i.layout(): self.clear_layout(i.layout())

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None: widget.deleteLater()
                else: self.clear_layout(item.layout())

    def update_weather_display(self, data):
        if not self.current_active_ver_id or self.current_active_ver_id not in self.weather_labels: return
        lbl = self.weather_labels[self.current_active_ver_id]
        if not data or "error" in data:
            lbl.setText("Unavailable")
            return
        desc = data.get("desc", "Unknown")
        temp = data.get("temp", 0)
        icon = data.get("icon", "")
        lbl.setText(f"{icon} {temp}°C\n{desc}")

    def fetch_weather(self, destination):
        if self.current_active_ver_id in self.weather_labels:
            self.weather_labels[self.current_active_ver_id].setText("Loading...")
        worker = WeatherWorker(self.api, destination)
        worker.finished_signal.connect(self.update_weather_display)
        self.start_worker(worker)

    # --- Trip Block Rendering ---
    def render_trip_block(self, title, plan_data, is_new=False, save=True):
        self.trip_counter += 1
        ver_id = self.trip_counter
        self.current_active_ver_id = ver_id 
        
        # 1. Sidebar Item
        list_item = QListWidgetItem(f"Ver {ver_id} - {title}")
        self.trip_list.addItem(list_item)
        
        # 2. Main Title
        lbl_title = QLabel(f"Ver {ver_id}: {title}")
        lbl_title.setStyleSheet("font-size: 24px; font-weight: 900; color: #1565c0; margin-top: 30px; margin-bottom: 10px;")
        self.feed_layout.insertWidget(self.feed_layout.count()-1, lbl_title)
        self.trip_widgets_map[id(list_item)] = lbl_title

        # --- 3. ROW 1: DASHBOARD ---
        dashboard_layout = QHBoxLayout()
        dashboard_layout.setSpacing(15)
        
        CARD_HEIGHT = 120
        CARD_STYLE = "background-color: white; border-radius: 10px; border: 1px solid #e0e0e0;"

        # -- A. Image Card --
        image_card = Card()
        image_card.setFixedSize(CARD_HEIGHT, CARD_HEIGHT) 
        image_card.setStyleSheet("background-color: transparent;") 
        ic_layout = QVBoxLayout(image_card)
        ic_layout.setContentsMargins(0, 0, 0, 0)
        ic_layout.setAlignment(Qt.AlignCenter)
        img_placeholder_layout = QVBoxLayout()
        img_placeholder_layout.setAlignment(Qt.AlignCenter)
        ic_layout.addLayout(img_placeholder_layout)
        self.image_placeholders[ver_id] = img_placeholder_layout
        dashboard_layout.addWidget(image_card)

        # -- B. Vibe Card --
        vibe_card = Card()
        vibe_card.setFixedHeight(CARD_HEIGHT)
        vibe_card.setStyleSheet(CARD_STYLE)
        vc_layout = QVBoxLayout(vibe_card)
        vc_layout.setContentsMargins(15, 15, 15, 15)
        vc_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        lbl_vibe_title = QLabel("TRIP VIBE")
        lbl_vibe_title.setStyleSheet("font-size: 10px; color: #757575; font-weight: bold; letter-spacing: 1px; border:none; background:transparent;")
        vibe_val = plan_data.get("analyzed_vibe", "General")
        lbl_vibe_text = QLabel(f"✨ {vibe_val}")
        lbl_vibe_text.setStyleSheet("font-size: 18px; font-weight: bold; color: #5e35b1; margin-top: 5px; border:none; background:transparent;")
        lbl_vibe_text.setWordWrap(True)
        vc_layout.addWidget(lbl_vibe_title)
        vc_layout.addWidget(lbl_vibe_text)
        dashboard_layout.addWidget(vibe_card)

        # -- C. Weather Card --
        weather_card = Card()
        weather_card.setFixedHeight(CARD_HEIGHT)
        weather_card.setStyleSheet(CARD_STYLE)
        wc_layout = QVBoxLayout(weather_card)
        wc_layout.setContentsMargins(15, 10, 15, 10)
        dest_name = plan_data.get("destination", "Trip")
        lbl_city = QLabel(dest_name.upper())
        lbl_city.setStyleSheet("font-size: 12px; font-weight: bold; color: #333; border:none; background:transparent;")
        wc_layout.addWidget(lbl_city)
        lbl_weather_stats = QLabel("--")
        lbl_weather_stats.setStyleSheet("font-size: 16px; color: #0277bd; font-weight: bold; border:none; background:transparent;")
        wc_layout.addWidget(lbl_weather_stats)
        self.weather_labels[ver_id] = lbl_weather_stats
        lbl_disclaimer = QLabel("Current weather (not trip time)")
        lbl_disclaimer.setStyleSheet("font-size: 9px; color: #888; font-style: italic; border:none; background:transparent;")
        wc_layout.addWidget(lbl_disclaimer)
        dashboard_layout.addWidget(weather_card)
        
        self.feed_layout.insertLayout(self.feed_layout.count()-1, dashboard_layout)

        # --- 4. ROW 2: LOGISTICS (Flights | Budget) ---
        logistics_layout = QHBoxLayout()
        logistics_layout.setSpacing(15)
        ROW2_HEIGHT = 220 

        # -- A. Flight Card --
        flight_card = Card()
        flight_card.setFixedHeight(ROW2_HEIGHT)
        flight_card.setStyleSheet(CARD_STYLE)
        fc_layout = QVBoxLayout(flight_card)
        fc_layout.setContentsMargins(15,15,15,15)
        
        lbl_flight_header = QLabel("✈️ Find Flights")
        lbl_flight_header.setStyleSheet("font-weight:bold; font-size:14px; color:#333; border:none;")
        fc_layout.addWidget(lbl_flight_header)

        # QStackedWidget requires proper import
        flight_stack = QStackedWidget()
        
        # View 1: Inputs (PRE-FILLED)
        input_widget = QWidget()
        in_layout = QVBoxLayout(input_widget); in_layout.setContentsMargins(0,0,0,0)
        
        origin_input = QLineEdit()
        pre_origin = plan_data.get("origin", "") 
        if pre_origin: origin_input.setText(pre_origin)
        else: origin_input.setPlaceholderText("From (e.g. London)")
        
        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        pre_date_str = plan_data.get("start_date", "")
        
        # Safe Date Parsing
        if pre_date_str:
            try:
                dt = QDate.fromString(pre_date_str, "yyyy-MM-dd")
                if dt.isValid(): date_input.setDate(dt)
                else: date_input.setDate(QDate.currentDate().addDays(30))
            except: date_input.setDate(QDate.currentDate().addDays(30))
        else:
            date_input.setDate(QDate.currentDate().addDays(30))
        
        btn_search = QPushButton("Search Flights")
        btn_search.setStyleSheet("background-color:#1976d2; color:white; padding:8px; border-radius:5px; font-weight:bold;")
        btn_search.setCursor(Qt.PointingHandCursor)
        
        in_layout.addWidget(QLabel("Origin:", styleSheet="border:none; color:#555;"))
        in_layout.addWidget(origin_input)
        in_layout.addWidget(QLabel("Departure:", styleSheet="border:none; color:#555;"))
        in_layout.addWidget(date_input)
        in_layout.addStretch()
        in_layout.addWidget(btn_search)
        
        flight_stack.addWidget(input_widget)

        # View 2: Results List
        results_list = QListWidget()
        results_list.setStyleSheet("border:none; background:transparent;")
        flight_stack.addWidget(results_list)
        
        fc_layout.addWidget(flight_stack)

        def on_search_click():
            orig = origin_input.text().strip()
            dest = dest_name
            date_str = date_input.date().toString("yyyy-MM-dd")
            if not orig: return
            btn_search.setText("Searching...")
            btn_search.setEnabled(False)
            
            def on_results(flights):
                btn_search.setText("Search Flights")
                btn_search.setEnabled(True)
                results_list.clear()
                flight_stack.setCurrentIndex(1)
                
                if not flights or "error" in flights:
                    results_list.addItem("No flights found.")
                    item_back = QListWidgetItem("⬅️ Try Again")
                    item_back.setTextAlignment(Qt.AlignCenter)
                    results_list.addItem(item_back)
                    return
                
                item_back = QListWidgetItem("⬅️ Back to Search")
                item_back.setFont(Qt.QFont("Arial", 10, Qt.QFont.Bold))
                results_list.addItem(item_back)

                for f in flights:
                    txt = f"{f.get('carrier')} | {f.get('dep')} -> {f.get('arr')} | {f.get('price')}"
                    item = QListWidgetItem(txt)
                    item.setToolTip(f"{f.get('stops')} stops")
                    results_list.addItem(item)

            worker = FlightWorker(self.api, orig, dest, date_str)
            worker.finished_signal.connect(on_results)
            self.start_worker(worker)
        
        def on_list_click(item):
            if "Back" in item.text() or "Try Again" in item.text():
                flight_stack.setCurrentIndex(0)

        results_list.itemClicked.connect(on_list_click)
        btn_search.clicked.connect(on_search_click)
        
        logistics_layout.addWidget(flight_card, 1)

        # -- B. Budget Pie Chart --
        budget_card = Card()
        budget_card.setFixedHeight(ROW2_HEIGHT)
        budget_card.setStyleSheet(CARD_STYLE)
        bc_layout = QVBoxLayout(budget_card)
        bc_layout.setContentsMargins(10,10,10,10)
        bc_layout.addWidget(QLabel("💰 Budget Plan (AI)", styleSheet="font-weight:bold; font-size:14px; color:#333; border:none;"))
        
        if BudgetPieChart:
            chart = BudgetPieChart()
            bc_layout.addWidget(chart)
            
            b_total = plan_data.get("budget", "2000")
            b_worker = BudgetWorker(self.api, b_total)
            b_worker.finished_signal.connect(chart.update_data)
            self.start_worker(b_worker)
        else:
            bc_layout.addWidget(QLabel("Chart Module Unavailable\n(Install PySide6-Charts)"))

        logistics_layout.addWidget(budget_card, 1)
        
        self.feed_layout.insertLayout(self.feed_layout.count()-1, logistics_layout)

        # --- 5. Itinerary Cards ---
        content_box = QWidget(); cv = QVBoxLayout(content_box)
        cv.setContentsMargins(0, 10, 0, 0)
        
        itinerary = plan_data.get("itinerary", [])
        for day in itinerary:
            day_card = Card()
            day_card.setStyleSheet(CARD_STYLE)
            d_layout = QVBoxLayout(day_card)
            d_layout.setContentsMargins(15, 15, 15, 15)
            
            d_title = QLabel(f"Day {day.get('day')}: {day.get('title')}")
            d_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; margin-bottom: 5px; border: none; background: transparent;")
            d_layout.addWidget(d_title)
            
            for act in day.get("activities", []): 
                act_lbl = QLabel(f"• {act}")
                act_lbl.setStyleSheet("font-size: 14px; color: #555; margin-left: 10px; border: none; background: transparent;")
                act_lbl.setWordWrap(True)
                d_layout.addWidget(act_lbl)
            
            cv.addWidget(day_card)
            
        self.feed_layout.insertWidget(self.feed_layout.count()-1, content_box)
        self.scroll_down()

        if save and not self.is_loading_mode:
            self.chat_history_state.append({"type": "plan", "content": {"title": title, "plan": plan_data}})
            self.save_state_to_server()

    # --- Image Handling ---
    def trigger_image_generation(self, destination, interest, ver_id):
        layout = self.image_placeholders.get(ver_id)
        if layout:
            lbl = QLabel("🎨")
            lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl)
            
        worker = ImageWorker(self.api, destination, interest)
        worker.finished_signal.connect(lambda b64: self.render_image_in_placeholder(b64, ver_id, save=True))
        self.start_worker(worker)

    def render_image_in_placeholder(self, b64, ver_id, save=True):
        layout = self.image_placeholders.get(ver_id)
        if not layout: return
        self.clear_layout(layout)
        if not b64:
            layout.addWidget(QLabel("No Image"))
            return
        try:
            data = base64.b64decode(b64)
            original_pix = QPixmap.fromImage(QImage.fromData(QByteArray(data)))
            size = 120
            radius = 10
            rounded_pix = QPixmap(size, size)
            rounded_pix.fill(Qt.transparent)
            painter = QPainter(rounded_pix)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            path = QPainterPath()
            path.addRoundedRect(0, 0, size, size, radius, radius)
            painter.setClipPath(path)
            scaled_pix = original_pix.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x_offset = (size - scaled_pix.width()) // 2
            y_offset = (size - scaled_pix.height()) // 2
            painter.drawPixmap(x_offset, y_offset, scaled_pix)
            painter.end()
            img_label = ClickableImage()
            img_label.setPixmap(rounded_pix)
            img_label.setFixedSize(size, size)
            img_label.clicked.connect(lambda: ImagePopup(original_pix).exec())
            layout.addWidget(img_label)
            if save and not self.is_loading_mode:
                self.chat_history_state.append({"type": "image", "content": b64})
                self.save_state_to_server()
        except Exception as e: 
            print(f"Img Error: {e}")
            layout.addWidget(QLabel("Error"))

    # --- Init & Load ---
    def init_new_trip(self, trip_response, username):
        self.is_loading_mode = False
        self.reset_ui()
        self.username = username
        self.trip_id = trip_response.get("trip_id")
        plan = trip_response
        dest = plan.get("destination", "Unknown")
        self.current_context = f"Dest: {dest}, Budget: {plan.get('budget', '?')}"
        self.current_plan_data = plan
        self.btn_pdf.setVisible(True)
        # Add simple error handling to prevent UI freeze
        try:
            self.render_trip_block("Initial Plan", plan, is_new=True)
        except Exception as e:
            print(f"Error rendering trip: {e}")
            self.feed_layout.addWidget(QLabel(f"Error rendering trip: {e}"))
            
        self.trigger_image_generation(dest, "travel", self.trip_counter)
        self.fetch_weather(dest)

    def load_existing_trip(self, full_data):
        self.is_loading_mode = True 
        self.reset_ui()
        self.trip_id = full_data.get("id")
        self.username = full_data.get("username", "")
        dest = full_data.get("destination", "")
        self.current_context = f"Dest: {dest}"
        for item in full_data.get("chat_history", []):
            t = item.get("type"); c = item.get("content")
            if t == "text": self.add_bubble(c, item.get("is_user"), save=False)
            elif t == "plan": 
                self.current_plan_data = c["plan"]
                self.render_trip_block(c["title"], c["plan"], save=False)
            elif t == "image": 
                self.render_image_in_placeholder(c, self.trip_counter, save=False)
        self.is_loading_mode = False
        if dest: self.fetch_weather(dest)
        if self.current_plan_data: # <--- הוסף את הבדיקה הזו
            self.btn_pdf.setVisible(True)
        QTimer.singleShot(150, lambda: self.scroll_area.verticalScrollBar().setValue(0))

    # --- Chat & Scroll ---
    def on_send(self):
        msg = self.chat_input.text().strip(); 
        if not msg: return
        self.chat_input.clear(); self.add_bubble(msg, True)
        if "Question" in self.mode_combo.currentText():
            loading = self.add_bubble("Thinking...", False)
            worker = ChatWorker(self.api, msg, self.current_context)
            worker.finished_signal.connect(lambda ans: self.update_bubble(loading, ans))
            self.start_worker(worker)
        else:
            loading = self.add_bubble("Refining plan...", False)
            def on_done(res):
                if res and "trip_plan" in res:
                    loading.deleteLater()
                    if self.chat_history_state: self.chat_history_state.pop()
                    new_plan = res["trip_plan"]
                    self.current_plan_data = new_plan
                    self.render_trip_block(f"Fix: {msg}", new_plan, is_new=True)
                    dest = new_plan.get("destination", "Trip")
                    self.trigger_image_generation(dest, msg, self.trip_counter)
                    if dest: self.fetch_weather(dest)
                else:
                    self.update_bubble(loading, f"Error: {res.get('error', 'Unknown')}")
            class RefineWorker(QThread):
                finished = Signal(dict)
                def __init__(self, api, plan, instr):
                    super().__init__(); self.api = api; self.plan = plan; self.instr = instr
                def run(self):
                    self.finished.emit(self.api.post("/refine_trip", {"current_plan": self.plan, "instruction": self.instr}))
            worker = RefineWorker(self.api, self.current_plan_data, msg)
            worker.finished.connect(on_done)
            self.start_worker(worker)

    def add_bubble(self, text, is_user, save=True):
        lbl = QLabel(text); lbl.setWordWrap(True)
        lbl.setStyleSheet("padding:10px; border-radius:10px; margin:5px;" + 
                         ("background:#e3f2fd; margin-left:40px;" if is_user else "background:white; margin-right:40px;"))
        self.feed_layout.insertWidget(self.feed_layout.count()-1, lbl); self.scroll_down()
        if save and not self.is_loading_mode:
            self.chat_history_state.append({"type": "text", "content": text, "is_user": is_user})
            self.save_state_to_server()
        return lbl

    def update_bubble(self, lbl, text):
        lbl.setText(text)
        if self.chat_history_state and not self.is_loading_mode:
            self.chat_history_state[-1]["content"] = text
            self.save_state_to_server()
        self.scroll_down()

    def save_state_to_server(self):
        if self.trip_id: 
            worker = StateSaverWorker(self.api, self.trip_id, self.chat_history_state)
            self.start_worker(worker)

    def scroll_down(self):
        if self.is_loading_mode: return
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))
    
    def scroll_to_item(self, item):
        w = self.trip_widgets_map.get(id(item))
        if w: self.scroll_area.ensureWidgetVisible(w)
        
    def save_pdf(self):
        print("🔘 Starting Rich PDF export...")

        if not hasattr(self, 'current_plan_data') or not self.current_plan_data:
            QMessageBox.warning(self, "No Trip", "No trip data available.")
            return

        # 1. חילוץ מזג האוויר מהמסך
        weather_text = "N/A"
        try:
            # אנו משתמשים ב-ID של הטיול הנוכחי כדי למצוא את הלייבל הנכון
            ver_id = self.current_active_ver_id
            if ver_id in self.weather_labels:
                weather_text = self.weather_labels[ver_id].text()
        except Exception as e:
            print(f"⚠️ Weather extract error: {e}")

        # 2. חילוץ התמונה מהמסך (Snapshot)
        temp_img_path = "temp_trip_snapshot.png"
        image_saved = False
        
        try:
            ver_id = self.current_active_ver_id
            # גישה ל-Layout שמחזיק את התמונה
            img_layout = self.image_placeholders.get(ver_id)
            
            if img_layout and img_layout.count() > 0:
                # אנו מניחים שהווידג'ט הראשון שם הוא התמונה (ClickableImage)
                item = img_layout.itemAt(0)
                widget = item.widget()
                
                if widget and hasattr(widget, 'pixmap') and widget.pixmap():
                    # שמירת ה-Pixmap לקובץ זמני
                    widget.pixmap().save(temp_img_path, "PNG")
                    image_saved = True
                    print("📸 Image snapshot captured!")
        except Exception as e:
            print(f"⚠️ Image snapshot error: {e}")

        # 3. שמירת ה-PDF
        dest_name = self.current_plan_data.get("destination", "Trip")
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Trip PDF", f"Trip_to_{dest_name}.pdf", "PDF Files (*.pdf)"
        )

        if filename:
            try:
                generate_trip_pdf(
                    self.current_plan_data, 
                    filename, 
                    image_path=temp_img_path if image_saved else None,
                    weather_info=weather_text
                )
                
                QMessageBox.information(self, "Success", "PDF saved successfully! 🚀")
                
                # מחיקת הקובץ הזמני
                if image_saved and os.path.exists(temp_img_path):
                    os.remove(temp_img_path)
                    
                # פתיחה אוטומטית
                import os
                os.startfile(filename) if os.name == 'nt' else None
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save PDF:\n{e}")
