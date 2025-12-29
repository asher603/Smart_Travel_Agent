import json
import base64
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                               QLineEdit, QComboBox, QScrollArea, QFrame, QSplitter, 
                               QListWidget, QListWidgetItem, QDialog, QSizePolicy)
from PySide6.QtCore import Qt, QThread, Signal, QByteArray, QTimer
from PySide6.QtGui import QPixmap, QImage
from client.components.custom_widgets import Card

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

# --- NEW: Weather Worker ---
class WeatherWorker(QThread):
    finished_signal = Signal(dict)
    def __init__(self, api, destination):
        super().__init__()
        self.api = api
        self.destination = destination

    def run(self):
        # Calls the new get_weather method in APIService
        result = self.api.get_weather(self.destination)
        self.finished_signal.emit(result)

class ImagePopup(QDialog):
    def __init__(self, pixmap, title="Trip Vibe"):
        super().__init__()
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        lbl_img = QLabel()
        lbl_img.setPixmap(pixmap.scaled(780, 580, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        lbl_img.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_img)
        layout.addWidget(QPushButton("Close", clicked=self.accept))

class TripScreen(QWidget):
    def __init__(self, switch_screen_callback, api):
        super().__init__()
        self.switch_screen = switch_screen_callback
        self.api = api
        self.trip_id = None
        self.username = ""
        self.trip_counter = 0
        self.trip_widgets_map = {}
        self.image_placeholders = {} 
        self.chat_history_state = [] 
        self.active_workers = []
        self.is_loading_mode = False
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        
        # --- Top Bar with Weather ---
        top = QHBoxLayout()
        btn_back = QPushButton("🔙 Back to Menu")
        btn_back.clicked.connect(self.go_back)
        top.addWidget(btn_back)
        
        top.addStretch()
        
        # New Weather Label
        self.weather_lbl = QLabel("")
        self.weather_lbl.setStyleSheet("font-size: 14px; color: #444; padding: 5px; border: 1px solid #ddd; border-radius: 5px; background: white;")
        self.weather_lbl.setVisible(False) # Hide until data arrives
        top.addWidget(self.weather_lbl)
        
        main_layout.addLayout(top)

        splitter = QSplitter(Qt.Horizontal)
        self.toc_widget = QWidget(); self.toc_widget.setFixedWidth(200)
        tl = QVBoxLayout(self.toc_widget)
        tl.addWidget(QLabel("📅 Versions")); self.trip_list = QListWidget()
        self.trip_list.itemClicked.connect(self.scroll_to_item)
        tl.addWidget(self.trip_list)
        
        self.scroll_area = QScrollArea(); self.scroll_area.setWidgetResizable(True)
        self.feed_cont = QWidget(); self.feed_layout = QVBoxLayout(self.feed_cont)
        self.feed_layout.addStretch(); self.scroll_area.setWidget(self.feed_cont)
        
        splitter.addWidget(self.toc_widget); splitter.addWidget(self.scroll_area)
        main_layout.addWidget(splitter)
        
        chat_box = QHBoxLayout(); self.chat_input = QLineEdit()
        self.chat_input.returnPressed.connect(self.on_send)
        self.mode_combo = QComboBox(); self.mode_combo.addItems(["❓ Question", "🛠️ Fix / New Trip"])
        btn_send = QPushButton("Send"); btn_send.clicked.connect(self.on_send)
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
        self.trip_counter = 0; self.trip_widgets_map = {}; self.image_placeholders = {}
        self.active_workers.clear()
        self.weather_lbl.setVisible(False) # Reset weather display
        while self.feed_layout.count() > 1:
            i = self.feed_layout.takeAt(0)
            if i.widget(): i.widget().deleteLater()

    def update_weather_display(self, data):
        """ Updates the weather label with data from the worker """
        if not data or "error" in data:
            self.weather_lbl.setText("Current Weather: Unavailable ⚠️")
            self.weather_lbl.setVisible(True)
            return

        desc = data.get("desc", "")
        temp = data.get("temp", 0)
        icon = data.get("icon", "")
        
        self.weather_lbl.setText(f"Current Weather: {icon} {desc}, {temp}°C")
        self.weather_lbl.setVisible(True)

    def fetch_weather(self, destination):
        """ Triggers the background weather fetch """
        self.weather_lbl.setText("Fetching weather... ⏳")
        self.weather_lbl.setVisible(True)
        worker = WeatherWorker(self.api, destination)
        worker.finished_signal.connect(self.update_weather_display)
        self.start_worker(worker)

    def init_new_trip(self, trip_response, username):
        self.is_loading_mode = False
        self.reset_ui()
        self.username = username
        self.trip_id = trip_response.get("trip_id")
        plan = trip_response
        
        dest = plan.get("destination", "Unknown")
        self.current_context = f"Dest: {dest}, Budget: {plan.get('budget', '?')}"
        self.current_plan_data = plan
        
        self.render_trip_block("Initial Plan", plan, is_new=True)
        self.trigger_image_generation(dest, "travel", self.trip_counter)
        
        # --- Fetch Weather ---
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
        
        # --- Fetch Weather ---
        if dest:
            self.fetch_weather(dest)

    def render_trip_block(self, title, plan_data, is_new=False, save=True):
        self.trip_counter += 1
        ver_id = self.trip_counter
        
        list_item = QListWidgetItem(f"Ver {ver_id} - {title}")
        self.trip_list.addItem(list_item)
        
        lbl_title = QLabel(f"Ver {ver_id}: {title}")
        lbl_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1565c0; margin-top: 20px;")
        self.feed_layout.insertWidget(self.feed_layout.count()-1, lbl_title)
        self.trip_widgets_map[id(list_item)] = lbl_title

        img_placeholder = QVBoxLayout() 
        container = QWidget(); container.setLayout(img_placeholder)
        self.feed_layout.insertWidget(self.feed_layout.count()-1, container)
        self.image_placeholders[ver_id] = img_placeholder 

        content_box = QWidget(); cv = QVBoxLayout(content_box)
        vibe = plan_data.get("analyzed_vibe")
        if vibe: cv.addWidget(QLabel(f"✨ Vibe: {vibe}", styleSheet="color: purple; font-weight:bold;"))
        
        itinerary = plan_data.get("itinerary", [])
        for day in itinerary:
            card = Card(); cl = QVBoxLayout(card)
            cl.addWidget(QLabel(f"Day {day.get('day')}: {day.get('title')}", styleSheet="font-weight:bold;"))
            for act in day.get("activities", []): cl.addWidget(QLabel(f"• {act}"))
            cv.addWidget(card)
        self.feed_layout.insertWidget(self.feed_layout.count()-1, content_box)
        self.scroll_down()

        if save and not self.is_loading_mode:
            self.chat_history_state.append({"type": "plan", "content": {"title": title, "plan": plan_data}})
            self.save_state_to_server()

    def trigger_image_generation(self, destination, interest, ver_id):
        worker = ImageWorker(self.api, destination, interest)
        worker.finished_signal.connect(lambda b64: self.render_image_in_placeholder(b64, ver_id, save=True))
        self.start_worker(worker)

    def render_image_in_placeholder(self, b64, ver_id, save=True):
        if not b64: return
        layout = self.image_placeholders.get(ver_id)
        if not layout: return

        try:
            data = base64.b64decode(b64)
            pix = QPixmap.fromImage(QImage.fromData(QByteArray(data)))
            
            btn = QPushButton("✨ Click to view trip vibe image")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { background-color: #e1f5fe; color: #0277bd; border: 1px solid #b3e5fc; 
                              border-radius: 10px; padding: 8px; font-weight: bold; text-align: left; }
                QPushButton:hover { background-color: #b3e5fc; }
            """)
            btn.clicked.connect(lambda: ImagePopup(pix).exec())
            
            layout.addWidget(btn)
            
            if save and not self.is_loading_mode:
                self.chat_history_state.append({"type": "image", "content": b64})
                self.save_state_to_server()
        except: pass

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
                    
                    # Update weather if destination changed
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
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))
    
    def scroll_to_item(self, item):
        w = self.trip_widgets_map.get(id(item))
        if w: self.scroll_area.ensureWidgetVisible(w)