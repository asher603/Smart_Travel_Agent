import base64
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QScrollArea, QFrame, QSplitter, 
    QListWidget, QListWidgetItem, QDialog, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QByteArray
from PySide6.QtGui import QPixmap

# --- IMPORTS ---
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
        
        # Chat
        chat_box = QHBoxLayout(); chat_box.setContentsMargins(10, 10, 10, 10)
        self.chat_input = QLineEdit(); self.chat_input.setPlaceholderText("Ask a question or request a change...")
        self.chat_input.returnPressed.connect(self.on_send)
        self.mode_combo = QComboBox(); self.mode_combo.addItems(["❓ Question", "🛠️ Fix / New Trip"])
        btn_send = QPushButton("➤"); btn_send.clicked.connect(self.on_send)
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
        self.back_signal.emit()

    def reset_ui(self):
        self.trip_list.clear(); self.chat_history_state = []
        self.trip_counter = 0; self.trip_widgets_map = {}; self.image_placeholders = {}; self.weather_labels = {}
        self.active_workers.clear()
        while self.feed_layout.count() > 1:
            i = self.feed_layout.takeAt(0)
            if i.widget(): i.widget().deleteLater()

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
        self.render_trip_block("Initial Plan", plan, is_new=True)
        # This call was failing because the method was missing:
        self.trigger_image_generation(dest, "travel", self.trip_counter)
        self.fetch_weather(dest)

    def load_existing_trip(self, full_data):
        self.is_loading_mode = True 
        self.reset_ui()
        self.trip_id = full_data.get("id") or full_data.get("_id")
        self.username = full_data.get("username", "")
        dest = full_data.get("destination", "")
        self.current_context = f"Dest: {dest}"
        
        history = full_data.get("chat_history", [])
        if not history and "destination" in full_data:
             self.render_trip_block("Saved Plan", full_data, save=False)
             self.current_plan_data = full_data
        else:
            for item in history:
                t = item.get("type"); c = item.get("content")
                if t == "text": self.add_bubble(c, item.get("is_user"), save=False)
                elif t == "plan": 
                    self.current_plan_data = c["plan"]
                    self.render_trip_block(c["title"], c["plan"], save=False)
                elif t == "image": 
                    self.render_image_in_placeholder(c, self.trip_counter, save=False)
        
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

        # 1. Flights
        flight_card = Card()
        flight_card.setFixedHeight(ROW2_HEIGHT)
        fc_layout = QVBoxLayout(flight_card)
        fc_layout.addWidget(QLabel("✈️ Flights", styleSheet="font-weight:bold; font-size:14px; color:#333;"))
        
        f_in_layout = QHBoxLayout()
        f_origin = QLineEdit(); f_origin.setPlaceholderText("From (e.g. London)")
        if plan_data.get("origin"): f_origin.setText(plan_data.get("origin"))
        btn_f = QPushButton("Search"); btn_f.setCursor(Qt.PointingHandCursor)
        f_in_layout.addWidget(f_origin); f_in_layout.addWidget(btn_f)
        fc_layout.addLayout(f_in_layout)
        
        f_list = QListWidget(); f_list.setStyleSheet("border:none; background:transparent;")
        fc_layout.addWidget(f_list)

        def do_flight_search():
            f_list.clear(); f_list.addItem("Searching...")
            w = FlightWorker(self.api, f_origin.text(), plan_data.get("destination"), plan_data.get("start_date"))
            w.finished_signal.connect(lambda res: update_flights(res, f_list))
            self.start_worker(w)

        def update_flights(res, list_w):
            list_w.clear()
            for f in res:
                list_w.addItem(f"{f['carrier']} | {f['price']} | {f['stops']}")

        btn_f.clicked.connect(do_flight_search)
        row2.addWidget(flight_card, 1)

        # 2. Budget
        budget_card = Card()
        budget_card.setFixedHeight(ROW2_HEIGHT)
        bc_layout = QVBoxLayout(budget_card)
        bc_layout.addWidget(QLabel("💰 Budget Breakdown", styleSheet="font-weight:bold; font-size:14px; color:#333;"))
        
        self.lbl_budget = QLabel("Loading...")
        self.lbl_budget.setWordWrap(True)
        self.lbl_budget.setStyleSheet("font-size:14px; color:#444;")
        bc_layout.addWidget(self.lbl_budget)
        bc_layout.addStretch()
        
        bw = BudgetWorker(self.api, plan_data.get("budget", "2000"))
        bw.finished_signal.connect(lambda res: self.lbl_budget.setText("\n".join([f"• {k}: {v}" for k,v in res.items()])))
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

    # --- THIS WAS THE MISSING METHOD ---
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
                "C:/My Projects/Smart_Travel_Agent/client/assets/globe_logo.png" 
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
        
        mode = self.mode_combo.currentText()
        if "Question" in mode:
            w = ChatWorker(self.api, msg, self.current_context)
            w.finished_signal.connect(lambda ans: self.add_bubble(ans, False))
            self.start_worker(w)
        else:
            self.add_bubble("Refining Plan...", False)
            w = RefineWorker(self.api, self.current_plan_data, msg)
            w.finished.connect(lambda res: self.on_refine_done(res, msg))
            self.start_worker(w)

    def on_refine_done(self, res, msg):
        if res and "trip_plan" in res:
             self.current_plan_data = res["trip_plan"]
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
        if self.trip_id:
            w = StateSaverWorker(self.api, self.trip_id, self.chat_history_state)
            self.start_worker(w)

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