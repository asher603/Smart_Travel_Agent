import json
import base64
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                               QLineEdit, QComboBox, QScrollArea, QFrame, QSplitter, 
                               QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, QThread, Signal, QByteArray, QTimer
from PySide6.QtGui import QPixmap, QImage

from client.components.custom_widgets import Card
from client.logic.workers import TripWorker

# --- סגנון (CSS) ---
STYLESHEET = """
    QWidget { font-family: 'Segoe UI', Arial, sans-serif; }
    
    QListWidget { border: none; background: #fafafa; border-right: 1px solid #ddd; }
    QListWidget::item { padding: 10px; border-bottom: 1px solid #eee; }
    QListWidget::item:selected { background: #e3f2fd; color: #1565c0; border-left: 4px solid #1565c0; }
    
    QLabel#Title { font-size: 18px; font-weight: bold; color: #1565c0; }
"""

# --- Worker לתמונה ---
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
            if response and "image_base64" in response: self.finished_signal.emit(response["image_base64"])
            else: self.finished_signal.emit(None)
        except: self.finished_signal.emit(None)

# --- Worker לצ'אט (מתחבר לתיקון שעשינו בשרת) ---
class ChatWorker(QThread):
    finished_signal = Signal(str)
    
    def __init__(self, api, question, context):
        super().__init__()
        self.api = api
        self.question = question
        self.context = context

    def run(self):
        try:
            # שליחת השאלה לשרת (Endpoint: /ask_question)
            response = self.api.post("/ask_question", {
                "question": self.question,
                "context": self.context
            })
            if response and "answer" in response:
                self.finished_signal.emit(response["answer"])
            else:
                self.finished_signal.emit("Sorry, no response from server.")
        except Exception as e:
            self.finished_signal.emit(f"Error: {str(e)}")


class TripResultWindow(QWidget):
    """
    חלון עצמאי המציג את פיד הטיול, הצ'אט וההיסטוריה.
    """
    def __init__(self, api, user, trip_data):
        super().__init__()
        self.api = api
        self.user = user
        self.trip_data = trip_data 
        
        self.setWindowTitle(f"Trip to {trip_data['dest']} ✈️")
        self.resize(1100, 800)
        self.setStyleSheet(STYLESHEET)
        
        self.trip_counter = 0
        self.trip_widgets_map = {}
        # אתחול ההקשר הבסיסי
        self.current_context = f"Destination: {trip_data['dest']}\nBudget: {trip_data['budg']}\nInterests: {trip_data['interest']}\n"

        self.setup_ui()
        # יצירת הטיול הראשון אוטומטית
        QTimer.singleShot(500, lambda: self.generate_trip_block("Initial Plan"))

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # צד ימין (רשימה)
        self.toc_widget = QWidget()
        self.toc_widget.setFixedWidth(220)
        self.toc_widget.setStyleSheet("background: #fdfdfd; border-right: 1px solid #ccc;")
        toc_l = QVBoxLayout(self.toc_widget)
        toc_l.addWidget(QLabel("📅 Versions", styleSheet="font-weight:bold; color:#546e7a; padding:10px;"))
        self.trip_list = QListWidget()
        self.trip_list.itemClicked.connect(self.scroll_to_item)
        toc_l.addWidget(self.trip_list)
        
        # מרכז (פיד)
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
        splitter.setCollapsible(0, False)
        main_layout.addWidget(splitter)
        
        # תחתית (צ'אט)
        chat_frame = QFrame()
        chat_frame.setStyleSheet("background: white; border-top: 1px solid #ccc;")
        chat_frame.setFixedHeight(80)
        cl = QHBoxLayout(chat_frame)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["❓ Question", "🛠️ Fix / New Trip"])
        self.mode_combo.setFixedWidth(130)
        self.mode_combo.setStyleSheet("border: 1px solid #ccc; border-radius: 4px; padding: 5px;")
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your request here...")
        self.chat_input.setStyleSheet("border: 1px solid #ccc; border-radius: 4px; padding: 8px;")
        self.chat_input.returnPressed.connect(self.on_send)
        
        btn_send = QPushButton("Send ➤")
        btn_send.setStyleSheet("background: #2e7d32; color: white; border-radius: 4px; padding: 8px 15px; font-weight: bold; border: none;")
        btn_send.setCursor(Qt.PointingHandCursor)
        btn_send.clicked.connect(self.on_send)
        
        cl.addWidget(self.mode_combo)
        cl.addWidget(self.chat_input)
        cl.addWidget(btn_send)
        main_layout.addWidget(chat_frame)

    def on_send(self):
        msg = self.chat_input.text().strip()
        if not msg: return
        
        mode = self.mode_combo.currentText()
        self.chat_input.clear()
        
        # הוספת הבועה של המשתמש
        self.add_bubble(msg, is_user=True)
        
        if "Question" in mode:
            # --- אופציה 1: שאלה אמיתית לשרת ---
            # מפעילים את הבוט כדי שיראה "חושב..."
            loading_lbl = self.add_bubble("🤔 Thinking...", is_user=False)
            
            # יצירת ה-Worker וחיבורו
            self.chat_worker = ChatWorker(self.api, msg, self.current_context)
            # כשהתשובה מגיעה -> מעדכנים את הבועה
            self.chat_worker.finished_signal.connect(lambda ans: self.update_bubble(loading_lbl, ans))
            self.chat_worker.start()
            
            # מעדכנים את ההקשר כדי שיזכור את השאלה
            self.current_context += f"\nUser asked: {msg}"
            
        else:
            # --- אופציה 2: יצירת טיול חדש ---
            self.current_context += f"\nModification Request: {msg}"
            self.generate_trip_block(msg)

    def generate_trip_block(self, suffix):
        self.trip_counter += 1
        ver_name = f"Ver {self.trip_counter}"
        
        if self.trip_counter > 1:
            sep = QFrame()
            sep.setFixedHeight(2)
            sep.setStyleSheet("background: #37474f; margin-top: 30px; margin-bottom: 20px;")
            self.feed_layout.insertWidget(self.feed_layout.count()-1, sep)
            
        lbl = QLabel(f"Generating {ver_name}...")
        lbl.setObjectName("Title")
        self.feed_layout.insertWidget(self.feed_layout.count()-1, lbl)
        
        cont = QWidget()
        QVBoxLayout(cont).setContentsMargins(0,0,0,0)
        self.feed_layout.insertWidget(self.feed_layout.count()-1, cont)
        
        item = QListWidgetItem(f"{ver_name} - {suffix[:15]}")
        self.trip_list.addItem(item)
        self.trip_widgets_map[id(item)] = lbl
        
        self.worker = TripWorker(
            self.api, self.user,
            self.trip_data['dest'], self.trip_data['origin'], "",
            self.trip_data['budg'], "USD",
            self.current_context, self.trip_data['days']
        )
        self.worker.finished_signal.connect(lambda d: self.render_trip(cont, lbl, d))
        self.worker.start()
        
        self.img_worker = ImageWorker(self.api, self.trip_data['dest'], self.current_context)
        self.img_worker.finished_signal.connect(lambda b64: self.render_image(cont, b64))
        self.img_worker.start()
        
        self.scroll_down()

    def render_trip(self, cont, lbl, data):
        lbl.setText(lbl.text().replace("Generating", "Trip Plan:"))
        layout = cont.layout()
        if "error" in data:
            layout.addWidget(QLabel(f"Error: {data['error']}"))
            return
        tp = data.get("trip_plan", {})
        if isinstance(tp, str): tp = json.loads(tp)
        
        # שמירת התוצאה להקשר
        summary = tp.get("summary", "")
        self.current_context += f"\nLatest Plan Summary: {summary}"

        c1 = Card()
        l1 = QVBoxLayout(c1)
        l1.addWidget(QLabel(summary, wordWrap=True, styleSheet="font-size:14px; line-height:1.4;"))
        layout.addWidget(c1)
        
        for d in tp.get("itinerary", []):
            dc = Card()
            dl = QVBoxLayout(dc)
            dl.addWidget(QLabel(f"Day {d.get('day')}: {d.get('title')}", styleSheet="font-weight:bold; font-size:16px; color:#37474f"))
            for a in d.get("activities", []):
                dl.addWidget(QLabel(f"• {a}", wordWrap=True))
            layout.addWidget(dc)
        self.scroll_down()

    def render_image(self, cont, b64):
        if not b64: return
        try:
            data = base64.b64decode(b64)
            pix = QPixmap.fromImage(QImage.fromData(QByteArray(data)))
            lbl = QLabel()
            lbl.setPixmap(pix.scaledToWidth(700, Qt.SmoothTransformation))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("margin-bottom: 15px; border-radius: 10px; border: 4px solid white;")
            cont.layout().insertWidget(0, lbl)
        except: pass

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

    def update_bubble(self, lbl, new_text):
        """ פונקציה לעדכון הבועה כשהתשובה מגיעה """
        lbl.setText(new_text)
        self.scroll_down()

    def scroll_down(self):
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))
        
    def scroll_to_item(self, item):
        w = self.trip_widgets_map.get(id(item))
        if w: self.scroll_area.ensureWidgetVisible(w)