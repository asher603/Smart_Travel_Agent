import json
import base64
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                               QLineEdit, QComboBox, QScrollArea, QFrame, QSplitter, 
                               QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, QThread, Signal, QByteArray, QTimer
from PySide6.QtGui import QPixmap, QImage

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

# --- המסך הראשי ---
class TripScreen(QWidget):
    def __init__(self, switch_screen_callback, api):
        super().__init__()
        self.switch_screen = switch_screen_callback
        self.api = api
        self.trip_counter = 0
        self.trip_widgets_map = {}
        self.current_context = ""
        self.trip_data = {} # נשמור כאן את המידע המלא
        
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        
        # Top Bar
        top_bar = QHBoxLayout()
        back_btn = QPushButton("🔙 Back to Home")
        back_btn.setFixedSize(120, 30)
        back_btn.setStyleSheet("background: transparent; color: #333; border: 1px solid #ccc; border-radius: 5px;")
        back_btn.clicked.connect(lambda: self.switch_screen(1))
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
        
        # Main Feed
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
        
        # Chat / Action Bar
        chat_frame = QFrame()
        chat_frame.setStyleSheet("background: white; border-top: 1px solid #ccc;")
        chat_frame.setFixedHeight(70)
        cl = QHBoxLayout(chat_frame)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["❓ Question", "🛠️ Fix / New Trip"])
        self.mode_combo.setFixedWidth(140)
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask a question or request changes...")
        self.chat_input.returnPressed.connect(self.on_send)
        
        btn_send = QPushButton("Send ➤")
        btn_send.setStyleSheet("background: #1565c0; color: white; border-radius: 5px; padding: 5px 15px;")
        btn_send.clicked.connect(self.on_send)
        
        cl.addWidget(self.mode_combo)
        cl.addWidget(self.chat_input)
        cl.addWidget(btn_send)
        main_layout.addWidget(chat_frame)

    def display_trip(self, trip_data, username):
        # איפוס נתונים
        self.trip_list.clear()
        while self.feed_layout.count() > 1:
            item = self.feed_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        self.trip_data = trip_data
        self.username = username
        self.trip_counter = 0
        
        initial_plan = trip_data.get("trip_plan", {})
        
        # שליפת שם היעד (עכשיו זה יעבוד כי תיקנו את הטופס)
        destination = trip_data.get('destination', 'Unknown Destination')
        budget = trip_data.get('budget', 'Unknown')
        vibe = initial_plan.get("analyzed_vibe", "General")
        
        self.current_context = f"Dest: {destination}, Budget: {budget}, Vibe: {vibe}"
        
        self.render_trip_block("Initial Plan", initial_plan, is_new_generation=False)

    def render_trip_block(self, title, plan_data, is_new_generation=True):
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
        
        if "analyzed_vibe" in plan_data:
             cv.addWidget(QLabel(f"✨ AI Vibe: {plan_data['analyzed_vibe']}", styleSheet="color: #6a1b9a; font-weight: bold;"))

        # תמונה רק בגרסה הראשונה
        if self.trip_counter == 1:
             # מוודא שקיים יעד
             dest = self.trip_data.get('destination', '')
             self.img_worker = ImageWorker(self.api, dest, self.current_context)
             self.img_worker.finished_signal.connect(lambda b64: self.render_image(cv, b64))
             self.img_worker.start()

        # ימים
        for day in plan_data.get("itinerary", []):
            card = Card()
            cl = QVBoxLayout(card)
            cl.addWidget(QLabel(f"Day {day.get('day')}: {day.get('title')}", styleSheet="font-weight:bold; font-size:16px"))
            for act in day.get("activities", []):
                cl.addWidget(QLabel(f"• {act}"))
            cv.addWidget(card)

        self.feed_layout.insertWidget(self.feed_layout.count()-1, content_box)
        self.scroll_down()

    def render_image(self, layout, b64):
        if not b64: return
        try:
            data = base64.b64decode(b64)
            pix = QPixmap.fromImage(QImage.fromData(QByteArray(data)))
            lbl = QLabel()
            lbl.setPixmap(pix.scaledToWidth(600, Qt.SmoothTransformation))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("border-radius: 10px; margin-bottom: 10px;")
            layout.insertWidget(0, lbl)
        except: pass

    def on_send(self):
        msg = self.chat_input.text().strip()
        if not msg: return
        self.chat_input.clear()
        
        self.add_bubble(msg, is_user=True)
        mode = self.mode_combo.currentText()
        
        if "Question" in mode:
            # מצב שאלה רגיל
            loading = self.add_bubble("Thinking... 🤔", is_user=False)
            self.chat_worker = ChatWorker(self.api, msg, self.current_context)
            self.chat_worker.finished_signal.connect(lambda ans: self.update_bubble(loading, ans))
            self.chat_worker.start()
        else:
            # מצב עריכה (Refine)
            loading = self.add_bubble("Creating new version... 🛠️", is_user=False)
            
            # וידוא שיש לנו תוכנית לערוך
            if not self.trip_data or "trip_plan" not in self.trip_data:
                self.update_bubble(loading, "Error: No active trip to edit.")
                return

            current_plan = self.trip_data.get("trip_plan", {})
            
            # הגדרת ה-Worker הפנימי
            class RefineWorker(QThread):
                finished = Signal(dict)
                def __init__(self, api, plan, instr):
                    super().__init__()
                    self.api = api
                    self.plan = plan
                    self.instr = instr
                def run(self):
                    # שליחה לשרת
                    res = self.api.post("/refine_trip", {"current_plan": self.plan, "instruction": self.instr}, timeout=120)
                    self.finished.emit(res)

            self.refine_worker = RefineWorker(self.api, current_plan, msg)
            
            # מה קורה כשהתשובה חוזרת
            def on_refine_done(response):
                # בדיקת הצלחה
                if response and "trip_plan" in response:
                    self.update_bubble(loading, "Done! Added new version to the list 👈")
                    new_plan = response["trip_plan"]
                    
                    # הוספת הגרסה החדשה לרשימה ולמסך
                    self.render_trip_block(f"Fix: {msg}", new_plan, is_new_generation=False)
                    
                    # עדכון הזיכרון כדי שהשינוי הבא יהיה על הגרסה הזאת
                    self.trip_data["trip_plan"] = new_plan
                
                # טיפול בשגיאות
                elif response and "error" in response:
                    self.update_bubble(loading, f"Server Error: {response['error']}")
                else:
                    self.update_bubble(loading, "Unknown error occurred. Try again.")

            self.refine_worker.finished.connect(on_refine_done)
            self.refine_worker.start()
            
    def add_bubble(self, text, is_user):
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
        return lbl

    def update_bubble(self, lbl, text):
        lbl.setText(text)
        self.scroll_down()

    def scroll_down(self):
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def scroll_to_item(self, item):
        w = self.trip_widgets_map.get(id(item))
        if w: self.scroll_area.ensureWidgetVisible(w)