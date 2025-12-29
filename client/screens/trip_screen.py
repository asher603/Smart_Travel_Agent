import json
import base64
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                               QLineEdit, QComboBox, QScrollArea, QFrame, QSplitter, 
                               QListWidget, QListWidgetItem, QDialog, QSizePolicy)
from PySide6.QtCore import Qt, QThread, Signal, QByteArray, QTimer, QSize
from PySide6.QtGui import QPixmap, QImage, QIcon

from client.components.custom_widgets import Card

# --- Workers ---
class ImageWorker(QThread):
    finished_signal = Signal(str) 
    def __init__(self, api, destination, interest):
        super().__init__()
        self.api = api
        self.destination = destination
        self.interest = interest
    def run(self):
        try:
            response = self.api.post("/generate_image", {"destination": self.destination, "interest": self.interest})
            if response and "image_base64" in response: 
                self.finished_signal.emit(response["image_base64"])
            else: 
                self.finished_signal.emit(None)
        except: 
            self.finished_signal.emit(None)

class ChatWorker(QThread):
    finished_signal = Signal(str)
    def __init__(self, api, question, context):
        super().__init__()
        self.api = api
        self.question = question
        self.context = context
    def run(self):
        try:
            response = self.api.post("/ask_question", {"question": self.question, "context": self.context})
            if response and "answer" in response:
                self.finished_signal.emit(response["answer"])
            else:
                self.finished_signal.emit("Sorry, no response from server.")
        except Exception as e:
            self.finished_signal.emit(f"Error: {str(e)}")

class StateSaverWorker(QThread):
    """שומר את המצב ברקע"""
    def __init__(self, api, trip_id, history):
        super().__init__()
        self.api = api
        self.trip_id = trip_id
        self.history = history
    def run(self):
        self.api.post("/update_trip_state", {"trip_id": self.trip_id, "chat_history": self.history})

# --- Image Popup Window ---
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
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

# --- Main Screen ---
class TripScreen(QWidget):
    def __init__(self, switch_screen_callback, api):
        super().__init__()
        self.switch_screen = switch_screen_callback
        self.api = api
        
        self.trip_id = None
        self.username = ""
        self.trip_counter = 0
        self.trip_widgets_map = {}
        self.current_context = ""
        self.current_plan_data = {} 
        self.chat_history_state = []
        
        self.is_loading_mode = False
        
        # --- תיקון הקריסה: רשימה לניהול ה-Threads הפעילים ---
        self.active_workers = []

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        
        # Top Bar
        top_bar = QHBoxLayout()
        back_btn = QPushButton("🔙 Back to Menu")
        back_btn.setFixedSize(120, 30)
        back_btn.setStyleSheet("background: transparent; color: #333; border: 1px solid #ccc; border-radius: 5px;")
        back_btn.clicked.connect(self.go_back)
        top_bar.addWidget(back_btn)
        top_bar.addStretch()
        main_layout.addLayout(top_bar)

        splitter = QSplitter(Qt.Horizontal)
        
        # Sidebar
        self.toc_widget = QWidget()
        self.toc_widget.setFixedWidth(200)
        self.toc_widget.setStyleSheet("background: #fdfdfd; border-right: 1px solid #ccc;")
        toc_l = QVBoxLayout(self.toc_widget)
        toc_l.addWidget(QLabel("📅 Versions", styleSheet="font-weight:bold; color:#546e7a; padding:10px;"))
        self.trip_list = QListWidget()
        self.trip_list.itemClicked.connect(self.scroll_to_item)
        toc_l.addWidget(self.trip_list)
        
        # Feed
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: #f4f6f8; border: none;")
        self.feed_container = QWidget()
        self.feed_layout = QVBoxLayout(self.feed_container)
        self.feed_layout.setContentsMargins(40, 40, 40, 40)
        self.feed_layout.setSpacing(20)
        self.feed_layout.addStretch()
        self.scroll_area.setWidget(self.feed_container)
        
        splitter.addWidget(self.toc_widget)
        splitter.addWidget(self.scroll_area)
        main_layout.addWidget(splitter)
        
        # Chat Bar
        chat_frame = QFrame()
        chat_frame.setStyleSheet("background: white; border-top: 1px solid #ccc;")
        chat_frame.setFixedHeight(70)
        cl = QHBoxLayout(chat_frame)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["❓ Question", "🛠️ Fix / New Trip"])
        self.mode_combo.setFixedWidth(140)
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type here...")
        self.chat_input.returnPressed.connect(self.on_send)
        
        btn_send = QPushButton("Send ➤")
        btn_send.setStyleSheet("background: #1565c0; color: white; border-radius: 5px; padding: 5px 15px;")
        btn_send.clicked.connect(self.on_send)
        
        cl.addWidget(self.mode_combo)
        cl.addWidget(self.chat_input)
        cl.addWidget(btn_send)
        main_layout.addWidget(chat_frame)

    # --- Worker Management (מונע קריסות) ---
    def start_worker(self, worker):
        """פונקציית עזר לניהול זיכרון של תהליכונים"""
        self.active_workers.append(worker)
        worker.finished.connect(lambda: self.cleanup_worker(worker))
        worker.start()

    def cleanup_worker(self, worker):
        if worker in self.active_workers:
            self.active_workers.remove(worker)
        worker.deleteLater()

    def go_back(self):
        if not self.is_loading_mode:
            self.save_state_to_server()
        self.switch_screen(1)

    def reset_ui(self):
        self.trip_list.clear()
        self.chat_history_state = []
        self.trip_counter = 0
        self.trip_widgets_map = {}
        
        # ניקוי כל ה-Workers הפעילים כדי למנוע התנגשויות
        self.active_workers.clear()

        while self.feed_layout.count() > 1:
            item = self.feed_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    # --- Logic ---

    def init_new_trip(self, trip_response, username):
        self.is_loading_mode = False
        self.reset_ui()
        self.username = username
        self.trip_id = trip_response.get("trip_id")
        
        plan = trip_response
        dest = plan.get("destination", "Trip")
        budget = plan.get("budget", "?")
        
        self.current_context = f"Dest: {dest}, Budget: {budget}"
        self.current_plan_data = plan
        
        # הצגת הטקסט
        self.render_trip_block("Initial Plan", plan, is_new=True)
        
        # יצירת תמונה
        if dest:
            worker = ImageWorker(self.api, dest, "travel")
            worker.finished_signal.connect(lambda b64: self.render_image(b64, is_new=True))
            self.start_worker(worker) # שימוש ב-Start Worker הבטוח

    def load_existing_trip(self, full_trip_data):
        self.is_loading_mode = True
        self.reset_ui()
        self.username = full_trip_data.get("username", "")
        self.trip_id = full_trip_data.get("id")
        
        raw_data = full_trip_data.get("trip_data", {})
        self.current_context = f"Dest: {full_trip_data.get('destination')}, Budget: {raw_data.get('budget')}"
        
        saved_history = full_trip_data.get("chat_history", [])
        
        for item in saved_history:
            itype = item.get("type")
            content = item.get("content")
            
            if itype == "text":
                self.add_bubble(content, item.get("is_user"), save=False)
            elif itype == "plan":
                self.current_plan_data = content["plan"]
                self.render_trip_block(content["title"], content["plan"], is_new=False, save=False)
            elif itype == "image":
                self.render_image(content, is_new=False, save=False)
        
        self.is_loading_mode = False

    def render_trip_block(self, title, plan_data, is_new=False, save=True):
        # חילוץ נתונים
        itinerary = plan_data.get("itinerary", [])
        if not itinerary and "trip_plan" in plan_data:
            inner = plan_data["trip_plan"]
            if isinstance(inner, dict):
                itinerary = inner.get("itinerary", [])
        if not isinstance(itinerary, list): itinerary = []

        self.trip_counter += 1
        ver_name = f"Ver {self.trip_counter}"
        
        list_item = QListWidgetItem(f"{ver_name} - {title}")
        self.trip_list.addItem(list_item)
        
        lbl_title = QLabel(f"{ver_name}: {title}")
        lbl_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1565c0; margin-top: 20px;")
        self.feed_layout.insertWidget(self.feed_layout.count()-1, lbl_title)
        self.trip_widgets_map[id(list_item)] = lbl_title
        
        content_box = QWidget()
        cv = QVBoxLayout(content_box)
        
        vibe = plan_data.get("analyzed_vibe")
        if not vibe and "trip_plan" in plan_data:
             vibe = plan_data["trip_plan"].get("analyzed_vibe")
        if vibe:
             cv.addWidget(QLabel(f"✨ AI Vibe: {vibe}", styleSheet="color: #6a1b9a; font-weight: bold;"))

        for day in itinerary:
            card = Card()
            cl = QVBoxLayout(card)
            cl.addWidget(QLabel(f"Day {day.get('day')}: {day.get('title')}", styleSheet="font-weight:bold; font-size:16px"))
            for act in day.get("activities", []):
                cl.addWidget(QLabel(f"• {act}"))
            cv.addWidget(card)

        self.feed_layout.insertWidget(self.feed_layout.count()-1, content_box)
        self.scroll_down()

        if save and not self.is_loading_mode:
            self.chat_history_state.append({
                "type": "plan",
                "content": {"title": title, "plan": plan_data}
            })
            self.save_state_to_server()

    # --- תיקון: הצגת כפתור במקום תמונה ענקית ---
    def render_image(self, b64, is_new=False, save=True):
        if not b64: return
        try:
            # הכנת התמונה לפופ-אפ
            data = base64.b64decode(b64)
            pix = QPixmap.fromImage(QImage.fromData(QByteArray(data)))
            
            # יצירת הכפתור המעוצב
            btn_show_img = QPushButton("✨ I made a little image for you (Click to view)")
            btn_show_img.setCursor(Qt.PointingHandCursor)
            btn_show_img.setStyleSheet("""
                QPushButton {
                    background-color: #e1f5fe;
                    color: #0277bd;
                    border: 1px solid #b3e5fc;
                    border-radius: 15px;
                    padding: 10px;
                    font-weight: bold;
                    margin: 10px 0;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #b3e5fc;
                }
            """)
            
            # חיבור ללחיצה - פתיחת הפופ-אפ
            btn_show_img.clicked.connect(lambda: self.show_image_popup(pix))
            
            # הוספה ללייאוט
            # מנסים להוסיף לפני הבלוק האחרון (הטקסט) אם אנחנו ביצירה חדשה
            # כדי שזה יראה "מעל" הטקסט
            count = self.feed_layout.count()
            if count > 2 and is_new:
                 self.feed_layout.insertWidget(count - 2, btn_show_img)
            else:
                 self.feed_layout.insertWidget(count - 1, btn_show_img)
            
            if save and not self.is_loading_mode:
                self.chat_history_state.append({
                    "type": "image",
                    "content": b64
                })
                self.save_state_to_server()
        except: pass

    def show_image_popup(self, pixmap):
        popup = ImagePopup(pixmap)
        popup.exec()

    def add_bubble(self, text, is_user, save=True):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        if is_user:
            lbl.setStyleSheet("background:#e3f2fd; color:#1565c0; padding:10px; border-radius:10px; margin-left:50px;")
            lbl.setAlignment(Qt.AlignRight)
        else:
            lbl.setStyleSheet("background:white; border:1px solid #ddd; padding:10px; border-radius:10px; margin-right:50px;")
            lbl.setAlignment(Qt.AlignLeft)
        
        self.feed_layout.insertWidget(self.feed_layout.count()-1, lbl)
        self.scroll_down()
        
        if save and not self.is_loading_mode:
            self.chat_history_state.append({
                "type": "text",
                "content": text,
                "is_user": is_user
            })
            self.save_state_to_server()
        
        return lbl

    def update_bubble(self, lbl, text):
        lbl.setText(text)
        if self.chat_history_state:
            last = self.chat_history_state[-1]
            if last["type"] == "text" and not last.get("is_user"):
                last["content"] = text
                if not self.is_loading_mode:
                    self.save_state_to_server()
        self.scroll_down()

    def save_state_to_server(self):
        if self.trip_id and not self.is_loading_mode:
            worker = StateSaverWorker(self.api, self.trip_id, self.chat_history_state)
            self.start_worker(worker) # שימוש ב-Start Worker הבטוח

    def on_send(self):
        msg = self.chat_input.text().strip()
        if not msg: return
        self.chat_input.clear()
        
        self.add_bubble(msg, is_user=True)
        mode = self.mode_combo.currentText()
        
        if "Question" in mode:
            loading = self.add_bubble("Thinking... 🤔", is_user=False)
            worker = ChatWorker(self.api, msg, self.current_context)
            worker.finished_signal.connect(lambda ans: self.update_bubble(loading, ans))
            self.start_worker(worker)
        else:
            # Refine
            loading = self.add_bubble("Creating new version... 🛠️", is_user=False)
            
            def on_refine_done(response):
                if response and "trip_plan" in response:
                    loading.deleteLater()
                    if self.chat_history_state:
                         self.chat_history_state.pop() 
                    
                    new_plan = response["trip_plan"]
                    self.current_plan_data = new_plan
                    self.render_trip_block(f"Fix: {msg}", new_plan)
                else:
                    self.update_bubble(loading, "Error generating plan.")

            class RefineWorker(QThread):
                finished = Signal(dict)
                def __init__(self, api, plan, instr):
                    super().__init__()
                    self.api = api; self.plan = plan; self.instr = instr
                def run(self):
                    res = self.api.post("/refine_trip", {"current_plan": self.plan, "instruction": self.instr})
                    self.finished.emit(res)
            
            worker = RefineWorker(self.api, self.current_plan_data, msg)
            worker.finished.connect(on_refine_done)
            self.start_worker(worker)

    def scroll_down(self):
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def scroll_to_item(self, item):
        w = self.trip_widgets_map.get(id(item))
        if w: self.scroll_area.ensureWidgetVisible(w)