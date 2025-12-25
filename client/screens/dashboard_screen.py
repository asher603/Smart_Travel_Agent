import json
import os
import requests
import tempfile
import scipy.io.wavfile as wav

# בדיקה אם יש ספריית הקלטה
try:
    import sounddevice as sd
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("⚠️ sounddevice not installed. Mic feature disabled.")

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                               QLineEdit, QSpinBox, QComboBox, 
                               QScrollArea, QMessageBox, QFrame, QSplitter)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPainter, QFont

try:
    from PySide6.QtCharts import QChart, QChartView, QPieSeries
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False

from client.components.custom_widgets import Card
from client.logic.workers import TripWorker

# --- Worker להקלטת סאונד (רץ ברקע) ---
class AudioRecorderWorker(QThread):
    finished_signal = Signal(str) # מחזיר את הטקסט המתומלל מהשרת
    
    def __init__(self, api_url):
        super().__init__()
        self.api_url = api_url

    def run(self):
        if not AUDIO_AVAILABLE: return

        try:
            duration = 5  # שניות הקלטה
            fs = 44100    # תדר דגימה
            
            print("🎙️ Recording started...")
            # הקלטה בפועל (חוסמת את ה-Thread הזה אבל לא את הממשק)
            recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
            sd.wait() 
            print("⏹️ Recording finished.")
            
            # שמירה לקובץ WAV זמני
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                wav.write(tmp.name, fs, recording)
                tmp_path = tmp.name
            
            # שליחה לשרת (Hugging Face Whisper)
            with open(tmp_path, 'rb') as f:
                response = requests.post(f"{self.api_url}/transcribe", files={"file": f}, timeout=30)
            
            os.remove(tmp_path) # ניקוי
            
            if response.status_code == 200:
                text = response.json().get("text", "")
                self.finished_signal.emit(text)
            else:
                self.finished_signal.emit(f"Error: Server failed ({response.status_code})")
                
        except Exception as e:
            print(f"Audio Error: {e}")
            self.finished_signal.emit(f"Error: {str(e)}")


class DashboardScreen(QWidget):
    def __init__(self, switch_cb, api):
        super().__init__()
        self.switch_cb, self.api = switch_cb, api
        self.curr_user = None
        
        main = QVBoxLayout(self)
        main.setContentsMargins(15, 15, 15, 15)
        main.setSpacing(10)
        
        # --- Header ---
        top = QHBoxLayout()
        self.lbl_welcome = QLabel("Hello!")
        self.lbl_welcome.setObjectName("Header")
        
        btn_hist = QPushButton("📜 History")
        btn_hist.setObjectName("SecondaryBtn")
        btn_hist.setCursor(Qt.PointingHandCursor)
        btn_hist.clicked.connect(lambda: self.switch_cb("history", self.curr_user))
        
        btn_out = QPushButton("Logout")
        btn_out.setCursor(Qt.PointingHandCursor)
        btn_out.setStyleSheet("""
            QPushButton { color: #d32f2f; border: 1px solid #ef9a9a; border-radius: 6px; padding: 6px 15px; font-weight: bold; background: white; }
            QPushButton:hover { background-color: #ffebee; border-color: #d32f2f; }
        """)
        btn_out.clicked.connect(lambda: self.switch_cb("login", None))
        
        top.addWidget(self.lbl_welcome)
        top.addStretch()
        top.addWidget(btn_hist)
        top.addSpacing(10)
        top.addWidget(btn_out)
        main.addLayout(top)

        # --- Split Layout ---
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(2)
        
        self.left_panel = QWidget()
        self.create_input_panel()
        
        self.right_panel = QWidget()
        self.create_results_panel()
        
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([400, 800])
        self.splitter.setCollapsible(0, False)
        
        main.addWidget(self.splitter)

    def create_input_panel(self):
        outer = QVBoxLayout(self.left_panel)
        outer.setContentsMargins(0,0,10,0)
        
        # כרטיס הטופס
        card = QFrame()
        card.setObjectName("Card")
        cl = QVBoxLayout(card)
        cl.setSpacing(12)
        cl.setContentsMargins(20,20,20,20)

        cl.addWidget(QLabel("Plan New Trip ✈️", objectName="SectionTitle"))
        
        # שדות רגילים
        cl.addWidget(QLabel("Origin:", objectName="InputLabel"))
        self.origin = QLineEdit()
        self.origin.setPlaceholderText("e.g. Tel Aviv")
        cl.addWidget(self.origin)

        cl.addWidget(QLabel("Destination:", objectName="InputLabel"))
        self.dest = QLineEdit()
        self.dest.setPlaceholderText("e.g. Tokyo")
        cl.addWidget(self.dest)
        
        cl.addWidget(QLabel("Stops (Opt):", objectName="InputLabel"))
        self.stops = QLineEdit()
        self.stops.setPlaceholderText("e.g. Dubai")
        cl.addWidget(self.stops)

        # שורת ימים
        r1 = QHBoxLayout()
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("Duration:", objectName="InputLabel"))
        self.days = QSpinBox()
        self.days.setRange(1, 60)
        self.days.setSuffix(" Days")
        self.days.setValue(5)
        self.days.setFixedHeight(35)
        v1.addWidget(self.days)
        r1.addLayout(v1)
        cl.addLayout(r1)
        
        # --- אזור העניין + מיקרופון ---
        cl.addWidget(QLabel("Interest / Vibe:", objectName="InputLabel"))
        
        mic_layout = QHBoxLayout()
        self.interest = QLineEdit()
        self.interest.setPlaceholderText("e.g. 'I want relax & good food'")
        self.interest.setFixedHeight(35)
        
        self.btn_mic = QPushButton("🎤")
        self.btn_mic.setToolTip("Hold to Record (5s)")
        self.btn_mic.setFixedSize(40, 35)
        self.btn_mic.setCursor(Qt.PointingHandCursor)
        # עיצוב כפתור הקלטה
        self.btn_mic.setStyleSheet("""
            QPushButton { background-color: #ef5350; color: white; border-radius: 6px; font-size: 16px; border: none; }
            QPushButton:hover { background-color: #e53935; }
            QPushButton:disabled { background-color: #ffcdd2; }
        """)
        self.btn_mic.clicked.connect(self.start_recording)
        
        mic_layout.addWidget(self.interest)
        mic_layout.addWidget(self.btn_mic)
        cl.addLayout(mic_layout)
        # ------------------------------

        # תקציב
        cl.addWidget(QLabel("Budget:", objectName="InputLabel"))
        r2 = QHBoxLayout()
        self.curr = QComboBox()
        self.curr.addItems(["$ USD", "₪ ILS", "€ EUR"])
        self.curr.setFixedWidth(80)
        self.curr.setFixedHeight(35)
        
        self.budg = QSpinBox()
        self.budg.setRange(100, 1000000)
        self.budg.setValue(2000)
        self.budg.setFixedHeight(35)
        
        r2.addWidget(self.curr)
        r2.addWidget(self.budg)
        cl.addLayout(r2)
        
        cl.addSpacing(10)
        self.btn_go = QPushButton("✨ Generate Trip")
        self.btn_go.setObjectName("PrimaryBtn")
        self.btn_go.setMinimumHeight(45)
        self.btn_go.setCursor(Qt.PointingHandCursor)
        self.btn_go.clicked.connect(self.go)
        cl.addWidget(self.btn_go)
        cl.addStretch()
        
        scroll = QScrollArea()
        scroll.setWidget(card)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        outer.addWidget(scroll)

    def create_results_panel(self):
        l = QVBoxLayout(self.right_panel)
        l.setContentsMargins(5,0,0,0)
        
        self.res_scroll = QScrollArea()
        self.res_scroll.setWidgetResizable(True)
        self.res_scroll.setStyleSheet("""
            QScrollArea { border: 1px solid #e0e0e0; border-radius: 12px; background-color: #f8f9fa; }
            QWidget#ResContent { background-color: #f8f9fa; }
        """)
        
        self.res_content = QWidget()
        self.res_content.setObjectName("ResContent")
        self.res_l = QVBoxLayout(self.res_content)
        self.res_l.setSpacing(20)
        self.res_l.setContentsMargins(30,30,30,30)
        
        self.ph = QLabel("👈 Use the form or 🎤 Microphone\nto tell me what you want!")
        self.ph.setAlignment(Qt.AlignCenter)
        self.ph.setStyleSheet("color: #90a4ae; font-size: 18px; font-weight: bold;")
        self.res_l.addWidget(self.ph)
        self.res_l.addStretch()
        
        self.res_scroll.setWidget(self.res_content)
        l.addWidget(self.res_scroll)

    def start_recording(self):
        if not AUDIO_AVAILABLE:
            QMessageBox.warning(self, "Error", "Audio library not found.")
            return

        self.btn_mic.setText("⏳") # אייקון המתנה
        self.btn_mic.setEnabled(False)
        self.interest.setPlaceholderText("Recording... Speak now!")
        
        # שליחת בקשה לשרת דרך Thread נפרד
        self.audio_worker = AudioRecorderWorker(self.api.base_url)
        self.audio_worker.finished_signal.connect(self.on_recording_finished)
        self.audio_worker.start()

    def on_recording_finished(self, text):
        self.btn_mic.setText("🎤")
        self.btn_mic.setEnabled(True)
        
        if text.startswith("Error"):
            QMessageBox.warning(self, "Recording Failed", text)
            self.interest.setPlaceholderText("e.g. 'I want relax'")
        else:
            # מנקים רווחים ומכניסים את הטקסט לשדה
            self.interest.setText(text.strip())

    def go(self):
        if not self.dest.text() or not self.origin.text():
            QMessageBox.warning(self, "Missing Info", "Origin & Destination required")
            return
            
        self.btn_go.setText("Analyzing & Planning... ⏳")
        self.btn_go.setEnabled(False)
        self.clear_res()
        
        # הודעת טעינה מפורטת
        lbl = QLabel("🤖 AI is listening, classifying, and planning...\n(Whisper -> HF Classifier -> LangChain)")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #1565c0; font-size: 16px;")
        self.res_l.addWidget(lbl)
        self.res_l.addStretch()

        # שליחה ל-TripWorker הרגיל
        self.worker = TripWorker(
            self.api, self.curr_user, 
            self.dest.text(), self.origin.text(), self.stops.text(),
            self.budg.value(), self.curr.currentText(),
            self.interest.text(), self.days.value()
        )
        self.worker.finished_signal.connect(self.show_res)
        self.worker.start()

    def clear_res(self):
        for i in reversed(range(self.res_l.count())):
            w = self.res_l.itemAt(i).widget()
            if w: w.setParent(None)

    def show_res(self, data):
        self.btn_go.setText("✨ Generate Trip")
        self.btn_go.setEnabled(True)
        self.clear_res()
        
        if "error" in data:
            err = QLabel(f"Error: {data['error']}")
            err.setStyleSheet("color: red; font-size: 16px;")
            self.res_l.addWidget(err)
            self.res_l.addStretch()
            return

        tp = data.get("trip_plan", {})
        if isinstance(tp, str): tp = json.loads(tp)
        
        # כרטיס סיכום
        c = Card()
        l = QVBoxLayout(c)
        l.addWidget(QLabel(f"✈️ Trip to {self.dest.text()}", styleSheet="font-size: 26px; font-weight: 900; color: #1565c0;"))
        
        # --- הצגת העניין שזוהה (כולל מהדיבור!) ---
        detected = tp.get("detected_interest", self.interest.text())
        # תווית ירוקה שמראה שה-AI הבין
        l.addWidget(QLabel(f"🧠 AI understood: <b>{detected}</b>", styleSheet="color: #2e7d32; background: #e8f5e9; padding: 8px; border-radius: 6px; font-size: 14px; margin-top: 5px; border: 1px solid #c8e6c9;"))
        
        l.addWidget(QLabel(tp.get("summary", ""), wordWrap=True, styleSheet="font-size: 16px; margin-top: 15px; line-height: 1.5; color: #333;"))
        self.res_l.addWidget(c)
        
        # גרף עוגה (QtCharts)
        if "budget_breakdown" in tp and CHARTS_AVAILABLE:
            cc = Card()
            cc.setMinimumHeight(400)
            cl = QVBoxLayout(cc)
            
            s = QPieSeries()
            for k,v in tp["budget_breakdown"].items(): s.append(k,v)
            if s.slices(): 
                s.slices()[0].setExploded(True)
                s.slices()[0].setLabelVisible(True)
                
            ch = QChart()
            ch.addSeries(s)
            ch.setTitle("Budget Breakdown")
            ch.setAnimationOptions(QChart.SeriesAnimations)
            ch.setTheme(QChart.ChartThemeBlueCerulean)
            ch.legend().setAlignment(Qt.AlignBottom)
            
            cv = QChartView(ch)
            cv.setRenderHint(QPainter.Antialiasing)
            cl.addWidget(cv)
            self.res_l.addWidget(cc)

        # כרטיסי ימים
        for d in tp.get("itinerary", []):
            dc = Card()
            dl = QVBoxLayout(dc)
            dl.addWidget(QLabel(f"Day {d.get('day')}: {d.get('title')}", styleSheet="font-size: 18px; font-weight: bold; color: #37474f;"))
            dl.addSpacing(5)
            for a in d.get("activities", []): 
                dl.addWidget(QLabel(f"• {a}", wordWrap=True, styleSheet="font-size: 14px; margin-bottom: 2px;"))
            self.res_l.addWidget(dc)
            
        self.res_l.addStretch()

    def set_user(self, u):
        self.curr_user = u
        self.lbl_welcome.setText(f"Welcome, {u} 👋")