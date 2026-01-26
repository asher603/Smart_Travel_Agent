import base64
import os
import re
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QScrollArea, QFrame, QSplitter, 
    QListWidget, QListWidgetItem, QDialog, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QByteArray
from PySide6.QtGui import QPixmap
from .workers import (
    ImageWorker, ChatWorker, StateSaverWorker, 
    WeatherWorker, FlightWorker, BudgetWorker, RefineWorker
)

try:
    from components import GlassCard as Card
except ImportError:
    class Card(QFrame):
        def __init__(self):
            super().__init__()
            self.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #e0e0e0;")

try:
    from utils.pdf_generator import generate_trip_pdf
except ImportError:
    generate_trip_pdf = None

try:
    from components import BudgetPieChart
except ImportError as e:
    BudgetPieChart = None
    print(f"❌ Budget Pie Chart not found: {e}")

# --- HELPER CLASSES ---
class ClickableImage(QLabel):
    clicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent); self.setCursor(Qt.PointingHandCursor)
    def mousePressEvent(self, e): self.clicked.emit(); super().mousePressEvent(e)

class ImagePopup(QDialog):
    def __init__(self, pixmap):
        super().__init__()
        self.resize(900, 700)
        l = QVBoxLayout(self)
        lbl = QLabel(); lbl.setPixmap(pixmap.scaled(880, 680, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        l.addWidget(lbl)

# --- MAIN VIEW ---
class TripViewerView(QWidget):
    back_signal = Signal()
    state_updated_signal = Signal(list)

    def __init__(self):
        super().__init__()
        self.api = None
        self.trip_id = None
        self.username = ""
        self.trip_counter = 0
        self.trip_widgets_map = {}
        self.image_placeholders = {} 
        self.weather_labels = {} 
        self.chat_history_state = [] 
        self.active_workers = []
        self.is_loading_mode = False
        self.current_active_ver_id = None 

        self.setup_ui()

    def set_api(self, api_service):
        self.api = api_service

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        
        # Top Bar
        top = QHBoxLayout(); top.setContentsMargins(10, 10, 10, 0)
        btn_back = QPushButton("🔙 Back to Menu")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(self.go_back)
        top.addWidget(btn_back)
        top.addStretch()
        
        self.btn_pdf = QPushButton("📄 Download PDF")
        self.btn_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_pdf.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 6px 12px; border-radius: 5px;")
        self.btn_pdf.clicked.connect(self.save_pdf)
        self.btn_pdf.setVisible(False)
        top.addWidget(self.btn_pdf)
        main_layout.addLayout(top)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        self.toc_widget = QWidget(); self.toc_widget.setFixedWidth(200)
        tl = QVBoxLayout(self.toc_widget)
        tl.addWidget(QLabel("📅 Versions"))
        self.trip_list = QListWidget(); self.trip_list.itemClicked.connect(self.scroll_to_item)
        tl.addWidget(self.trip_list)
        
        # Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
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

        # Mode Selector
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["❓ Question", "🛠️ Fix / New Trip"])

        # AI Model Selector
        self.model_combo = QComboBox()
        self.model_combo.addItems(["Gemini", "Groq", "Ollama"])
        self.model_combo.setToolTip("Select AI Model")
        self.model_combo.setFixedWidth(80)

        # Chat Input
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask a question or request a change...")
        self.chat_input.returnPressed.connect(self.on_send)

        # Send Button
        btn_send = QPushButton("➤")
        btn_send.clicked.connect(self.on_send)
        btn_send.setCursor(Qt.PointingHandCursor)
        btn_send.setToolTip("Send Message (or press Enter)")

        # Chat Box
        chat_box = QHBoxLayout()
        chat_box.setContentsMargins(10, 10, 10, 10)
        chat_box.addWidget(self.mode_combo)
        chat_box.addWidget(self.model_combo)
        chat_box.addWidget(self.chat_input)
        chat_box.addWidget(btn_send)
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
        self.back_signal.emit()

    def clear_layout(self, layout):
        """
        function to recursively clear a layout of all its widgets and sub-layouts.
        """
        if not layout: return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                # If this is an internal Layout (like a row), we enter it and clear it as well
                self.clear_layout(item.layout())

    def reset_ui(self):
        # 1. עצירת תהליכים ברקע (מונע התנגשויות ועדכוני רפאים)
        for w in self.active_workers:
            try:
                w.blockSignals(True)  # חוסם את האותות כדי שלא ינסו לעדכן UI
                if w.isRunning():
                    w.quit()
                    w.wait(50)  # מחכה מעט לסגירה מסודרת
            except: pass
        self.active_workers.clear()

        # 2. איפוס משתנים
        self.trip_list.clear()
        self.chat_history_state = []
        self.trip_counter = 0
        self.trip_widgets_map = {}
        self.image_placeholders = {} 
        self.weather_labels = {}
        self.current_active_ver_id = None

        # 3. ניקוי עמוק של המסך באמצעות הפונקציה החדשה
        if self.feed_layout:
            self.clear_layout(self.feed_layout)
            # החזרת ה-"Stretch" התחתון שדוחף את הכל למעלה
            self.feed_layout.addStretch()

    def init_new_trip(self, trip_response, username):
        self.is_loading_mode = False
        self.reset_ui()
        self.username = username
        self.trip_id = trip_response.get("trip_id")
        plan = trip_response
        dest = plan.get("destination", "Unknown")
        self.current_plan_data = plan
        self.current_context = json.dumps(plan, default=str, indent=2)
        self.btn_pdf.setVisible(True)
        self.render_trip_block("Initial Plan", plan, is_new=True)
        # Trigger Image Gen
        self.trigger_image_generation(dest, "travel", self.trip_counter)
        self.fetch_weather(dest)

    def load_existing_trip(self, full_data):
        self.is_loading_mode = True 
        self.reset_ui()
        
        # זיהוי מזהה הטיול בצורה רובסטית
        self.trip_id = full_data.get("id") or full_data.get("_id") or full_data.get("trip_id")
        self.username = full_data.get("username", "")
        dest = full_data.get("destination", "")
        self.current_context = f"Dest: {dest}"
        
        # --- התיקון הקריטי כאן ---
        # מעתיקים את ההיסטוריה מהשרת לזיכרון המקומי
        # זה מבטיח שהודעה חדשה תתווסף לרשימה הקיימת ולא תדרוס אותה
        self.chat_history_state = full_data.get("chat_history", [])
        
        # משתמשים במשתנה המקומי לציור המסך
        history = self.chat_history_state
        
        if not history and "destination" in full_data:
             self.render_trip_block("Saved Plan", full_data, save=False)
             self.current_plan_data = full_data
        else:
            for item in history:
                t = item.get("type")
                c = item.get("content")
                if t == "text": 
                    self.add_bubble(c, item.get("is_user"), save=False)
                elif t == "plan": 
                    self.current_plan_data = c["plan"]
                    self.render_trip_block(c["title"], c["plan"], save=False)
                elif t == "image": 
                    self.render_image_in_placeholder(c, self.trip_counter, save=False)
        
        # עדכון הקונטקסט ל-AI
        if hasattr(self, 'current_plan_data') and self.current_plan_data:
            self.current_context = json.dumps(self.current_plan_data, default=str, indent=2)
        else:
            self.current_context = json.dumps(full_data, default=str, indent=2)

        self.is_loading_mode = False
        if dest: self.fetch_weather(dest)
        if hasattr(self, 'current_plan_data'): self.btn_pdf.setVisible(True)
        
    def render_trip_block(self, title, plan_data, is_new=False, save=True):
        self.trip_counter += 1
        ver_id = self.trip_counter
        self.current_active_ver_id = ver_id 
        
        item = QListWidgetItem(f"Ver {ver_id} - {title}")
        self.trip_list.addItem(item)
        
        lbl = QLabel(f"Version {ver_id}: {title}")
        lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #1565c0; margin-top:20px;")
        self.feed_layout.insertWidget(self.feed_layout.count()-1, lbl)
        self.trip_widgets_map[id(item)] = lbl
        
        # --- ROW 1: DASHBOARD ---
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        CARD_HEIGHT = 160

        # 1. Image Card
        img_card = Card()
        img_card.setFixedSize(CARD_HEIGHT, CARD_HEIGHT)
        img_layout = QVBoxLayout(img_card)
        img_layout.setContentsMargins(0,0,0,0) 
        self.image_placeholders[ver_id] = img_layout 
        row1.addWidget(img_card)

        # 2. Vibe Card
        vibe_card = Card()
        vibe_card.setFixedHeight(CARD_HEIGHT)
        vc_layout = QVBoxLayout(vibe_card)
        vc_layout.setContentsMargins(15,15,15,15)
        
        vc_layout.addWidget(QLabel("✨ TRIP VIBE", styleSheet="font-size:12px; font-weight:bold; color:#555;"))
        vibe_text = plan_data.get("summary", "A great trip awaiting you!")
        lbl_vibe = QLabel(vibe_text)
        lbl_vibe.setWordWrap(True) 
        lbl_vibe.setStyleSheet("font-size:14px; color:#5e35b1; font-weight:500;")
        lbl_vibe.setAlignment(Qt.AlignTop)
        vc_layout.addWidget(lbl_vibe)
        vc_layout.addStretch()
        row1.addWidget(vibe_card, 3) 

        # 3. Weather Card
        weather_card = Card()
        weather_card.setFixedHeight(CARD_HEIGHT)
        wc_layout = QVBoxLayout(weather_card)
        wc_layout.setContentsMargins(15,15,15,15)
        wc_layout.addWidget(QLabel(plan_data.get("destination", "").upper(), styleSheet="font-size:12px; font-weight:bold; color:#555;"))
        
        lbl_w = QLabel("--"); 
        self.weather_labels[ver_id] = lbl_w
        lbl_w.setStyleSheet("font-size:24px; color:#0277bd; font-weight:bold;")
        lbl_w.setAlignment(Qt.AlignCenter)
        wc_layout.addWidget(lbl_w)
        
        wc_layout.addWidget(QLabel("Current Forecast", styleSheet="font-size:10px; color:#888; alignment:center;"))
        wc_layout.addStretch()
        row1.addWidget(weather_card, 1)

        self.feed_layout.insertLayout(self.feed_layout.count()-1, row1)

        # --- ROW 2: LOGISTICS ---
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        ROW2_HEIGHT = 220

        # 1. Flights (UPDATED SECTION)
        flight_card = Card()
        flight_card.setFixedHeight(ROW2_HEIGHT)
        fc_layout = QVBoxLayout(flight_card)
        fc_layout.addWidget(QLabel("✈️ Flights", styleSheet="font-weight:bold; font-size:14px; color:#333;"))
        
        origin_city = plan_data.get("origin", "Tel Aviv")
        btn_f = QPushButton(f"🔎 Check Flights from {origin_city}")
        btn_f.setCursor(Qt.PointingHandCursor)
        btn_f.setStyleSheet("""
            QPushButton {
                background-color: #e3f2fd; 
                color: #1565c0; 
                border: 1px solid #bbdefb;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #bbdefb; }
        """)
        fc_layout.addWidget(btn_f)
        
        f_list = QListWidget(); f_list.setStyleSheet("border:none; background:transparent;")
        fc_layout.addWidget(f_list)

        def do_flight_search():
            f_list.clear(); f_list.addItem("Searching...")
            # Use the origin from the variable directly
            w = FlightWorker(self.api, origin_city, plan_data.get("destination"), plan_data.get("start_date"))
            w.finished_signal.connect(lambda res: update_flights(res, f_list))
            self.start_worker(w)

        def update_flights(res, list_w):
            list_w.clear()
            if not res:
                list_w.addItem("No flights found.")
                return
            for f in res:
                list_w.addItem(f"{f['carrier']} | {f['price']} | {f['stops']}")

        btn_f.clicked.connect(do_flight_search)
        row2.addWidget(flight_card, 1)

        # 2. Budget
        budget_card = Card()
        budget_card.setFixedHeight(ROW2_HEIGHT)
        bc_layout = QVBoxLayout(budget_card)
        bc_layout.addWidget(QLabel("💰 Budget Breakdown", styleSheet="font-weight:bold; font-size:14px; color:#333;"))
        
        # Instantiate Chart if available, else fallback
        current_chart = None
        if BudgetPieChart:
            current_chart = BudgetPieChart()
            bc_layout.addWidget(current_chart)
        else:
            lbl_fallback = QLabel("Chart Component Missing")
            lbl_fallback.setAlignment(Qt.AlignCenter)
            bc_layout.addWidget(lbl_fallback)
        
        bw = BudgetWorker(self.api, plan_data.get("budget", "2000"))
        # Pass the specific chart instance to the updater to avoid overwriting issues
        bw.finished_signal.connect(lambda res, c=current_chart: self.update_budget_chart(res, c))
        self.start_worker(bw)

        row2.addWidget(budget_card, 1)
        self.feed_layout.insertLayout(self.feed_layout.count()-1, row2)

        # --- ITINERARY ---
        for day in plan_data.get("itinerary", []):
            d_card = Card()
            d_card.setStyleSheet("background:white; border-radius:10px; padding:15px; margin-top:5px;")
            dl = QVBoxLayout(d_card)
            
            day_num = day.get('day')
            text = day.get('activity') or day.get('title') or "Activity"
            t_lbl = QLabel(f"Day {day_num}: {text}")
            t_lbl.setWordWrap(True) 
            t_lbl.setStyleSheet("font-weight:bold; font-size:16px; color:#1565c0;")
            dl.addWidget(t_lbl)
            
            if "activities" in day and isinstance(day["activities"], list):
                for act in day["activities"]:
                    a_lbl = QLabel(f"• {act}")
                    a_lbl.setWordWrap(True) 
                    a_lbl.setStyleSheet("font-size:14px; color:#444; margin-top:3px;")
                    dl.addWidget(a_lbl)
            
            self.feed_layout.insertWidget(self.feed_layout.count()-1, d_card)

        if save and not self.is_loading_mode:
            self.chat_history_state.append({"type": "plan", "content": {"title": title, "plan": plan_data}})
            self.save_state_to_server()

    def update_budget_chart(self, breakdown_data, chart_widget):
        """
        Parses the server response (formatted strings) into integers for the chart.
        Input: {"Flights": "$700 (35%)", ...}
        Output: Updates chart with {"Flights": 700, ...}
        """
        if not chart_widget or not breakdown_data:
            return

        clean_data = {}
        for category, text in breakdown_data.items():
            # Regex to extract the first number found (e.g. 700 from "$700 (35%)")
            match = re.search(r'(\d+)', str(text).replace(",", ""))
            if match:
                clean_data[category] = int(match.group(1))
            else:
                # Fallback: ignore or set to 0
                pass
        
        chart_widget.update_data(clean_data)

    def trigger_image_generation(self, destination, interest, ver_id):
        worker = ImageWorker(self.api, destination, interest)
        worker.finished_signal.connect(lambda b64: self.render_image_in_placeholder(b64, ver_id))
        self.start_worker(worker)

    def render_image_in_placeholder(self, b64, ver_id, save=True):
        l = self.image_placeholders.get(ver_id)
        if not l: return
        while l.count(): l.takeAt(0).widget().deleteLater()
        
        pix = QPixmap()
        loaded = False
        
        if b64:
            try:
                data = base64.b64decode(b64)
                pix.loadFromData(QByteArray(data))
                loaded = not pix.isNull()
            except: pass

        if not loaded:
            # Robust Path Handling
            base_dir = os.getcwd() 
            candidates = [
                os.path.join(base_dir, "assets", "globe_logo.png"),
                os.path.join(base_dir, "client", "assets", "globe_logo.png"),
            ]
            
            for path in candidates:
                if os.path.exists(path):
                    if pix.load(path):
                        loaded = True
                        break
            
            if not loaded:
                lbl = QLabel("No Image")
                lbl.setStyleSheet("color:#ccc; font-style:italic;")
                lbl.setAlignment(Qt.AlignCenter)
                l.addWidget(lbl)
                return

        lbl = ClickableImage()
        lbl.setPixmap(pix.scaled(158, 158, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        lbl.setAlignment(Qt.AlignCenter)
        lbl.clicked.connect(lambda: ImagePopup(pix).exec())
        l.addWidget(lbl)

        if save and not self.is_loading_mode:
            content = b64 if b64 else "" 
            self.chat_history_state.append({"type": "image", "content": content})
            self.save_state_to_server()

    def fetch_weather(self, dest):
        if ver_id := self.current_active_ver_id:
            lbl = self.weather_labels.get(ver_id)
            if lbl: lbl.setText("...")
        w = WeatherWorker(self.api, dest)
        w.finished_signal.connect(self.update_weather_ui)
        self.start_worker(w)

    def update_weather_ui(self, data):
        if not self.current_active_ver_id: return
        lbl = self.weather_labels.get(self.current_active_ver_id)
        if lbl and data:
            lbl.setText(f"{data.get('icon','')} {data.get('temp','--')}°C\n{data.get('desc','')}")
        elif lbl:
             lbl.setText("N/A")

    def on_send(self):
        msg = self.chat_input.text(); self.chat_input.clear()
        if not msg: return
        self.add_bubble(msg, True)
        
        selected_mode = self.mode_combo.currentText()
        selected_model = self.model_combo.currentText().lower()

        if "Question" in selected_mode:
            w = ChatWorker(self.api, msg, self.current_context, selected_model)
            w.finished_signal.connect(lambda ans: self.add_bubble(ans, False))
            self.start_worker(w)
        else:
            self.add_bubble("Refining Plan...", False)
            w = RefineWorker(self.api, self.trip_id, self.current_plan_data, msg, selected_model)
            w.finished.connect(lambda res: self.on_refine_done(res, msg))
            self.start_worker(w)

    def on_refine_done(self, res, msg):
        if res and "trip_plan" in res:
             self.current_plan_data = res["trip_plan"]
             self.current_context = json.dumps(res["trip_plan"], default=str, indent=2)
             self.render_trip_block(f"Fix: {msg}", res["trip_plan"], is_new=True)
        else:
             self.add_bubble("Failed to refine plan.", False)

    def add_bubble(self, text, is_user, save=True):
        lbl = QLabel(text); lbl.setWordWrap(True)
        lbl.setStyleSheet(f"background: {'#e3f2fd' if is_user else 'white'}; padding: 10px; border-radius: 10px;")
        self.feed_layout.insertWidget(self.feed_layout.count()-1, lbl)
        if save and not self.is_loading_mode:
            self.chat_history_state.append({"type": "text", "content": text, "is_user": is_user})
            self.save_state_to_server()

    def save_state_to_server(self):
       if not self.is_loading_mode:
            self.state_updated_signal.emit(self.chat_history_state)

    def scroll_to_item(self, item):
        w = self.trip_widgets_map.get(id(item))
        if w: self.scroll_area.ensureWidgetVisible(w)
        
    def save_pdf(self):
        if not generate_trip_pdf:
            QMessageBox.warning(self, "Error", "PDF Module missing")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Save Trip PDF", f"Trip_Plan.pdf", "PDF Files (*.pdf)")
        if filename:
            try:
                generate_trip_pdf(self.current_plan_data, filename)
                QMessageBox.information(self, "Success", "PDF Saved!")
                import os
                if os.name == 'nt': os.startfile(filename)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save PDF:\n{str(e)}")