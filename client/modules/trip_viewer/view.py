import base64
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QScrollArea, QFrame, QSplitter, 
    QListWidget, QListWidgetItem, QDialog, QMessageBox, QDateEdit
)
from PySide6.QtCore import Qt, Signal, QByteArray, QTimer, QDate
from PySide6.QtGui import QPixmap, QImage

# --- IMPORT WORKERS ---
from .workers import (
    ImageWorker, ChatWorker, StateSaverWorker, 
    WeatherWorker, FlightWorker, BudgetWorker, RefineWorker
)

# --- IMPORTS (Safety Checks) ---
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

# --- MAIN VIEW CLASS ---
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
        
        self.scroll_area = QScrollArea(); self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.feed_cont = QWidget(); self.feed_cont.setStyleSheet("background: transparent;")
        self.feed_layout = QVBoxLayout(self.feed_cont); self.feed_layout.setSpacing(20)
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
        """Called when generating a fresh trip"""
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
        self.trigger_image_generation(dest, "travel", self.trip_counter)
        self.fetch_weather(dest)

    def load_existing_trip(self, full_data):
        """Called when loading from History"""
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
        
        # --- DASHBOARD ROW (Image | Weather) ---
        dash_layout = QHBoxLayout()
        dash_layout.setSpacing(10)
        
        # 1. Image Card
        img_layout = QVBoxLayout(); self.image_placeholders[ver_id] = img_layout
        card_img = Card(); card_img.setLayout(img_layout)
        card_img.setFixedSize(140, 140) # Keep square
        dash_layout.addWidget(card_img)

        # 2. Weather Card
        card_weather = Card(); card_weather.setFixedHeight(140)
        w_layout = QVBoxLayout(card_weather); w_layout.setContentsMargins(15,15,15,15)
        
        lbl_city = QLabel(plan_data.get("destination", "Location").upper())
        lbl_city.setStyleSheet("font-size:12px; font-weight:bold; color:#555;")
        
        lbl_temp = QLabel("--"); self.weather_labels[ver_id] = lbl_temp
        lbl_temp.setStyleSheet("font-size:20px; font-weight:bold; color:#0277bd;")
        
        w_layout.addWidget(lbl_city); w_layout.addWidget(lbl_temp)
        dash_layout.addWidget(card_weather)

        self.feed_layout.insertLayout(self.feed_layout.count()-1, dash_layout)

        # --- ITINERARY ---
        for day in plan_data.get("itinerary", []):
            d_card = Card()
            d_card.setStyleSheet("background:white; border-radius:10px; padding:10px; margin-top:5px;")
            dl = QVBoxLayout(d_card)
            day_num = day.get('day')
            text = day.get('activity') or day.get('title') or "Activity"
            dl.addWidget(QLabel(f"Day {day_num}: {text}"))
            
            if "activities" in day and isinstance(day["activities"], list):
                for act in day["activities"]:
                    dl.addWidget(QLabel(f"• {act}"))
            
            self.feed_layout.insertWidget(self.feed_layout.count()-1, d_card)

        if save and not self.is_loading_mode:
            self.chat_history_state.append({"type": "plan", "content": {"title": title, "plan": plan_data}})
            self.save_state_to_server()

    def trigger_image_generation(self, destination, interest, ver_id):
        worker = ImageWorker(self.api, destination, interest)
        worker.finished_signal.connect(lambda b64: self.render_image_in_placeholder(b64, ver_id))
        self.start_worker(worker)

    def render_image_in_placeholder(self, b64, ver_id, save=True):
        l = self.image_placeholders.get(ver_id)
        if l:
            while l.count(): l.takeAt(0).widget().deleteLater()
            
            # --- FALLBACK LOGIC ---
            pix = QPixmap()
            loaded = False
            
            if b64:
                try:
                    data = base64.b64decode(b64)
                    pix.loadFromData(QByteArray(data))
                    loaded = not pix.isNull()
                except:
                    print("Base64 Decode Error")

            if not loaded:
                # Load fallback asset from client/assets/globe_logo.png
                fallback_path = os.path.join("assets", "globe_logo.png")
                if os.path.exists(fallback_path):
                     pix.load(fallback_path)
                else:
                     # Absolute fallback if file missing
                     l.addWidget(QLabel("No Image"))
                     return

            # Render the image (either AI or Fallback)
            if not pix.isNull():
                lbl = ClickableImage()
                lbl.setPixmap(pix.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                lbl.clicked.connect(lambda: ImagePopup(pix).exec())
                l.addWidget(lbl)
                l.setAlignment(Qt.AlignCenter)

            if save and not self.is_loading_mode:
                # Save the b64 content if valid, otherwise save nothing/flag
                content_to_save = b64 if loaded else ""
                self.chat_history_state.append({"type": "image", "content": content_to_save})
                self.save_state_to_server()

    def fetch_weather(self, dest):
        # This will call the REAL weather logic now
        if ver_id := self.current_active_ver_id:
            lbl = self.weather_labels.get(ver_id)
            if lbl: lbl.setText("Loading...")
            
        w = WeatherWorker(self.api, dest)
        w.finished_signal.connect(self.update_weather_ui)
        self.start_worker(w)

    def update_weather_ui(self, data):
        if not self.current_active_ver_id: return
        lbl = self.weather_labels.get(self.current_active_ver_id)
        if lbl and data:
            icon = data.get("icon", "")
            temp = data.get("temp", 0)
            desc = data.get("desc", "")
            lbl.setText(f"{icon} {temp}°C\n{desc}")

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
        lbl = QLabel(text); lbl.setStyleSheet(f"background: {'#e3f2fd' if is_user else 'white'}; padding: 10px; border-radius: 10px;")
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
        if generate_trip_pdf:
            generate_trip_pdf(self.current_plan_data, "trip.pdf")
            QMessageBox.information(self, "PDF", "Saved!")
        else:
            QMessageBox.warning(self, "Error", "PDF Module missing")