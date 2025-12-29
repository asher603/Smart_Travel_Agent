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

class StateSaverWorker(QThread):
    """שומר את המצב ברקע כדי לא לתקוע את הממשק"""
    def __init__(self, api, trip_id, history):
        super().__init__()
        self.api = api
        self.trip_id = trip_id
        self.history = history
    def run(self):
        self.api.post("/update_trip_state", {"trip_id": self.trip_id, "chat_history": self.history})

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
        
        # הרשימה שמחזיקה את כל ההיסטוריה לשחזור
        # כל איבר הוא מילון: {type: 'text'|'plan'|'image', content: ..., is_user: bool}
        self.chat_history_state = [] 

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

    def go_back(self):
        # לפני שיוצאים, מוודאים שהכל שמור (למרות שאנחנו שומרים תוך כדי)
        self.save_state_to_server()
        self.switch_screen(1) # חזרה לתפריט

    def reset_ui(self):
        self.trip_list.clear()
        self.chat_history_state = []
        self.trip_counter = 0
        self.trip_widgets_map = {}
        # מחיקת כל הוידג'טים בפיד
        while self.feed_layout.count() > 1: # משאירים את ה-Stretch
            item = self.feed_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    # --- פונקציה ראשית 1: יצירת טיול חדש ---
    def init_new_trip(self, trip_response, username):
        self.reset_ui()
        self.username = username
        self.trip_id = trip_response.get("trip_id")
        
        plan = trip_response.get("trip_plan", {})
        dest = trip_response.get("destination", "Unknown")
        budget = trip_response.get("budget", "?")
        
        self.current_context = f"Dest: {dest}, Budget: {budget}"
        self.current_plan_data = plan
        
        # רינדור ראשוני (שומר אוטומטית להיסטוריה)
        self.render_trip_block("Initial Plan", plan, is_new=True)
        
        # יצירת תמונה
        if dest:
            self.img_worker = ImageWorker(self.api, dest, "travel")
            self.img_worker.finished_signal.connect(lambda b64: self.render_image(b64, is_new=True))
            self.img_worker.start()

    # --- פונקציה ראשית 2: טעינת טיול קיים ---
    def load_existing_trip(self, full_trip_data):
        self.reset_ui()
        self.username = full_trip_data.get("username", "")
        self.trip_id = full_trip_data.get("id")
        
        # שחזור נתונים בסיסיים
        raw_data = full_trip_data.get("trip_data", {})
        self.current_context = f"Dest: {full_trip_data.get('destination')}, Budget: {raw_data.get('budget')}"
        
        # שחזור ההיסטוריה (Replay)
        saved_history = full_trip_data.get("chat_history", [])
        
        # אנחנו לא רוצים לשמור ב-DB בזמן שאנחנו משחזרים
        for item in saved_history:
            itype = item.get("type")
            content = item.get("content")
            
            if itype == "text":
                self.add_bubble(content, item.get("is_user"), save=False)
            elif itype == "plan":
                self.current_plan_data = content["plan"] # עדכון התוכנית האחרונה
                self.render_trip_block(content["title"], content["plan"], is_new=False, save=False)
            elif itype == "image":
                self.render_image(content, is_new=False, save=False)

    # --- Rendering Logic ---

    def render_trip_block(self, title, plan_data, is_new=False, save=True):
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

        for day in plan_data.get("itinerary", []):
            card = Card()
            cl = QVBoxLayout(card)
            cl.addWidget(QLabel(f"Day {day.get('day')}: {day.get('title')}", styleSheet="font-weight:bold; font-size:16px"))
            for act in day.get("activities", []):
                cl.addWidget(QLabel(f"• {act}"))
            cv.addWidget(card)

        self.feed_layout.insertWidget(self.feed_layout.count()-1, content_box)
        self.scroll_down()

        if save:
            self.chat_history_state.append({
                "type": "plan",
                "content": {"title": title, "plan": plan_data}
            })
            self.save_state_to_server()

    def render_image(self, b64, is_new=False, save=True):
        if not b64: return
        try:
            # מציאת המקום הנכון להוסיף (מתחת לכותרת האחרונה)
            # לטובת הפשטות, נוסיף פשוט לסוף הפיד, או נניח שזה תמיד אחרי התוכנית הראשונה
            
            data = base64.b64decode(b64)
            pix = QPixmap.fromImage(QImage.fromData(QByteArray(data)))
            lbl = QLabel()
            lbl.setPixmap(pix.scaledToWidth(600, Qt.SmoothTransformation))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("border-radius: 10px; margin: 10px 0;")
            
            # הכנסה לפני ה-Stretch
            self.feed_layout.insertWidget(self.feed_layout.count()-1, lbl)
            
            if save:
                self.chat_history_state.append({
                    "type": "image",
                    "content": b64
                })
                self.save_state_to_server()
        except: pass

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
        
        if save:
            self.chat_history_state.append({
                "type": "text",
                "content": text,
                "is_user": is_user
            })
            self.save_state_to_server()
        
        return lbl

    def update_bubble(self, lbl, text):
        lbl.setText(text)
        # עדכון ההיסטוריה (אנחנו צריכים לעדכן את האיבר האחרון שהוא הבוט)
        if self.chat_history_state:
            last = self.chat_history_state[-1]
            if last["type"] == "text" and not last.get("is_user"):
                last["content"] = text
                self.save_state_to_server()
        self.scroll_down()

    def save_state_to_server(self):
        if self.trip_id:
            # שימוש ב-Worker כדי לא לתקוע את ה-UI
            self.saver = StateSaverWorker(self.api, self.trip_id, self.chat_history_state)
            self.saver.start()

    def on_send(self):
        msg = self.chat_input.text().strip()
        if not msg: return
        self.chat_input.clear()
        
        self.add_bubble(msg, is_user=True)
        mode = self.mode_combo.currentText()
        
        if "Question" in mode:
            loading = self.add_bubble("Thinking... 🤔", is_user=False)
            self.chat_worker = ChatWorker(self.api, msg, self.current_context)
            self.chat_worker.finished_signal.connect(lambda ans: self.update_bubble(loading, ans))
            self.chat_worker.start()
        else:
            # Refine
            loading = self.add_bubble("Creating new version... 🛠️", is_user=False)
            
            # פונקציית עזר פנימית לטיפול בתשובה
            def on_refine_done(response):
                if response and "trip_plan" in response:
                    # מחיקת הבועה הזמנית של הטעינה מהמסך ומההיסטוריה (כדי שלא תשמר סתם)
                    loading.deleteLater()
                    self.chat_history_state.pop() 
                    
                    new_plan = response["trip_plan"]
                    self.current_plan_data = new_plan
                    self.render_trip_block(f"Fix: {msg}", new_plan)
                else:
                    self.update_bubble(loading, "Error generating plan.")

            # Worker ל-Refine
            class RefineWorker(QThread):
                finished = Signal(dict)
                def __init__(self, api, plan, instr):
                    super().__init__()
                    self.api = api; self.plan = plan; self.instr = instr
                def run(self):
                    res = self.api.post("/refine_trip", {"current_plan": self.plan, "instruction": self.instr})
                    self.finished.emit(res)
            
            self.rw = RefineWorker(self.api, self.current_plan_data, msg)
            self.rw.finished.connect(on_refine_done)
            self.rw.start()

    def scroll_down(self):
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def scroll_to_item(self, item):
        w = self.trip_widgets_map.get(id(item))
        if w: self.scroll_area.ensureWidgetVisible(w)