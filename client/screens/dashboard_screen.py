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

# Added QToolTip, QStackedWidget, QTextEdit, QPlainTextEdit to imports
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                               QLineEdit, QSpinBox, QComboBox, 
                               QScrollArea, QMessageBox, QFrame, QSplitter, QToolTip,
                               QStackedWidget, QTextEdit, QPlainTextEdit)
from PySide6.QtCore import Qt, QThread, Signal, QSize
# Added QCursor to imports
from PySide6.QtGui import QPainter, QFont, QColor, QCursor

try:
    from PySide6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False

from client.components.custom_widgets import Card
from client.logic.workers import TripWorker

# --- Central Stylesheet (Re-introduced to ensure buttons and inputs look correct) ---
STYLESHEET = """
    /* --- Basic Settings --- */
    QMainWindow { background-color: #f0f2f5; }
    QWidget { font-family: 'Segoe UI', Arial, sans-serif; }
    
    /* --- Text & Headers --- */
    QLabel { color: #263238; }
    QLabel#Header { font-size: 26px; font-weight: 900; color: #1565c0; }
    QLabel#SectionTitle { font-size: 18px; font-weight: bold; color: #37474f; margin-bottom: 5px; }
    QLabel#InputLabel { font-size: 14px; font-weight: 600; color: #546e7a; margin-top: 5px; }

    /* --- Text Fields --- */
    QLineEdit, QPlainTextEdit { 
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #cfd8dc;
        border-radius: 6px;
        padding: 8px 10px;
        font-size: 14px;
    }
    QLineEdit:focus, QPlainTextEdit:focus { border: 2px solid #2196f3; }

    /* --- Spin Boxes --- */
    QSpinBox {
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #cfd8dc;
        border-radius: 6px;
        padding: 8px 10px;
        font-size: 14px;
        min-height: 25px;
    }
    QSpinBox:focus { border: 2px solid #2196f3; }

    QSpinBox::up-button, QSpinBox::down-button {
        width: 20px; 
        background-color: #eceff1;
        border-left: 1px solid #cfd8dc;
    }
    QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: #cfd8dc; }

    /* --- ComboBox --- */
    QComboBox {
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #cfd8dc;
        border-radius: 6px;
        padding: 8px 10px;
        font-size: 14px;
        min-height: 25px;
    }
    QComboBox:focus { border: 2px solid #2196f3; }
    QComboBox QAbstractItemView {
        background-color: #ffffff;
        color: #333333;
        selection-background-color: #2196f3;
        selection-color: #ffffff;
    }

    /* --- Buttons --- */
    QPushButton#PrimaryBtn {
        background-color: #1565c0;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px;
        font-weight: bold;
        font-size: 16px;
    }
    QPushButton#PrimaryBtn:hover { background-color: #0d47a1; }
    QPushButton#PrimaryBtn:pressed { background-color: #002171; }
    QPushButton#PrimaryBtn:disabled { background-color: #b0bec5; color: #eceff1; }

    QPushButton#SecondaryBtn {
        background-color: white;
        color: #455a64;
        border: 1px solid #b0bec5;
        border-radius: 6px;
        padding: 6px 12px;
        font-weight: 600;
    }
    QPushButton#SecondaryBtn:hover { background-color: #f5f5f5; border: 1px solid #78909c; }
    
    /* --- Card --- */
    QFrame#Card {
        background-color: white;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
    }
"""

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
        
        # Apply Stylesheet
        self.setStyleSheet(STYLESHEET)
        
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
        
        # State for chat/refinement
        self.current_trip_context = "" 

    def create_input_panel(self):
        layout = QVBoxLayout(self.left_panel)
        layout.setContentsMargins(0,0,10,0)

        # Use StackedWidget to switch between Form and Chat
        self.left_stack = QStackedWidget()
        
        # Page 0: The Planning Form
        self.page_form = QWidget()
        self.setup_form_page(self.page_form)
        self.left_stack.addWidget(self.page_form)
        
        # Page 1: The Chat Interface
        self.page_chat = QWidget()
        self.setup_chat_page(self.page_chat)
        self.left_stack.addWidget(self.page_chat)
        
        layout.addWidget(self.left_stack)

    def setup_form_page(self, parent_widget):
        outer = QVBoxLayout(parent_widget)
        outer.setContentsMargins(0,0,0,0)
        
        # Scroll area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        card = QFrame()
        card.setObjectName("Card")
        cl = QVBoxLayout(card)
        cl.setSpacing(12)
        cl.setContentsMargins(20,20,20,20)

        cl.addWidget(QLabel("Plan New Trip ✈️", objectName="SectionTitle"))
        
        # Regular Fields
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

        # Duration
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
        
        # --- Interest / Vibe (Multi-line) ---
        cl.addWidget(QLabel("Interest / Vibe:", objectName="InputLabel"))
        
        mic_layout = QHBoxLayout()
        self.interest = QPlainTextEdit()
        self.interest.setPlaceholderText("e.g. 'I want relax & good food. Maybe some museums.'")
        self.interest.setFixedHeight(70) # Fixed height, scrollable
        
        self.btn_mic = QPushButton("🎤")
        self.btn_mic.setToolTip("Hold to Record (5s)")
        self.btn_mic.setFixedSize(40, 35)
        self.btn_mic.setCursor(Qt.PointingHandCursor)
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

        # Budget
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
        self.btn_go.setObjectName("PrimaryBtn") # Uses Stylesheet now
        self.btn_go.setMinimumHeight(45)
        self.btn_go.setCursor(Qt.PointingHandCursor)
        self.btn_go.clicked.connect(self.go)
        cl.addWidget(self.btn_go)
        cl.addStretch()
        
        scroll.setWidget(card)
        outer.addWidget(scroll)

    def setup_chat_page(self, parent_widget):
        # Layout for the Chat Interface (replacing the form)
        cl = QVBoxLayout(parent_widget)
        cl.setContentsMargins(0,0,0,0)
        
        card = QFrame()
        card.setObjectName("Card")
        l = QVBoxLayout(card)
        l.setContentsMargins(15,15,15,15)
        
        l.addWidget(QLabel("💬 Trip Assistant", objectName="SectionTitle"))
        
        # Chat History
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("border: none; background: #fafafa; font-size: 14px;")
        l.addWidget(self.chat_display)
        
        # Chat Input Area
        input_row = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("e.g. 'Make it cheaper' or 'Add a museum'")
        self.chat_input.returnPressed.connect(self.send_chat)
        
        btn_send = QPushButton("➤")
        btn_send.setFixedSize(40,35)
        btn_send.setObjectName("PrimaryBtn")
        btn_send.clicked.connect(self.send_chat)
        
        input_row.addWidget(self.chat_input)
        input_row.addWidget(btn_send)
        l.addLayout(input_row)
        
        l.addSpacing(10)
        
        # Start Over Button
        btn_reset = QPushButton("↺ Start Over")
        btn_reset.setObjectName("SecondaryBtn")
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.clicked.connect(self.reset_planning)
        l.addWidget(btn_reset)
        
        cl.addWidget(card)

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
            # For QPlainTextEdit we use setPlainText
            self.interest.setPlainText(text.strip())

    def go(self):
        if not self.dest.text() or not self.origin.text():
            QMessageBox.warning(self, "Missing Info", "Origin & Destination required")
            return
            
        # Switch to Chat Interface
        self.left_stack.setCurrentIndex(1)
        self.chat_display.clear()
        self.append_chat("System", "Generating your initial trip plan... 🤖")
        
        # Save initial context
        self.current_trip_context = self.interest.toPlainText()
        
        self.btn_go.setText("Generating...")
        self.clear_res()
        
        # Loading message
        lbl = QLabel("🤖 AI is planning your trip...")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #1565c0; font-size: 16px;")
        self.res_l.addWidget(lbl)
        self.res_l.addStretch()

        self.call_worker()

    def send_chat(self):
        msg = self.chat_input.text().strip()
        if not msg: return
        
        self.chat_input.clear()
        self.append_chat("You", msg)
        self.append_chat("System", "Refining plan... ⏳")
        
        # Update context: Append new instruction to original interest
        # This simulates "processing on top of original prompt"
        self.current_trip_context += f"\n[User Modification]: {msg}"
        
        self.call_worker()

    def call_worker(self):
        # Common method to call worker with current state
        self.worker = TripWorker(
            self.api, self.curr_user, 
            self.dest.text(), self.origin.text(), self.stops.text(),
            self.budg.value(), self.curr.currentText(),
            self.current_trip_context, # Uses accumulated context
            self.days.value()
        )
        self.worker.finished_signal.connect(self.show_res)
        self.worker.start()

    def reset_planning(self):
        # Wipe clean and start over
        self.left_stack.setCurrentIndex(0) # Back to form
        self.chat_display.clear()
        self.current_trip_context = ""
        self.btn_go.setText("✨ Generate Trip")
        self.clear_res()
        # Reset result view placeholder
        self.res_l.addWidget(self.ph)
        self.res_l.addStretch()

    def append_chat(self, sender, text):
        color = "#1565c0" if sender == "System" else "#2e7d32"
        self.chat_display.append(f"<b style='color:{color}'>{sender}:</b> {text}")

    def clear_res(self):
        for i in reversed(range(self.res_l.count())):
            w = self.res_l.itemAt(i).widget()
            if w: w.setParent(None)

    # --- Tooltip Handler ---
    def on_slice_hover(self, state, slice_obj):
        if state:
            if hasattr(slice_obj, 'data_tooltip'):
                QToolTip.showText(QCursor.pos(), slice_obj.data_tooltip)
        else:
            QToolTip.hideText()

    def show_res(self, data):
        self.btn_go.setText("✨ Generate Trip")
        # Ensure we are on the result/chat view (mainly for first run)
        self.clear_res()
        
        # If this came from a chat update, update chat log
        if self.left_stack.currentIndex() == 1:
             self.append_chat("System", "Plan updated! Check the details. ✅")
        
        if "error" in data:
            err = QLabel(f"Error: {data['error']}")
            err.setStyleSheet("color: red; font-size: 16px;")
            self.res_l.addWidget(err)
            self.res_l.addStretch()
            return

        tp = data.get("trip_plan", {})
        if isinstance(tp, str): tp = json.loads(tp)
        
        # Summary Card
        c = Card()
        l = QVBoxLayout(c)
        l.addWidget(QLabel(f"✈️ Trip to {self.dest.text()}", styleSheet="font-size: 26px; font-weight: 900; color: #1565c0;"))
        
        detected = tp.get("detected_interest", "")
        if detected:
            l.addWidget(QLabel(f"🧠 Focus: <b>{detected}</b>", styleSheet="color: #2e7d32; background: #e8f5e9; padding: 8px; border-radius: 6px; font-size: 14px; margin-top: 5px; border: 1px solid #c8e6c9;"))
        
        l.addWidget(QLabel(tp.get("summary", ""), wordWrap=True, styleSheet="font-size: 16px; margin-top: 15px; line-height: 1.5; color: #333;"))
        self.res_l.addWidget(c)
        
        # Chart
        if "budget_breakdown" in tp and CHARTS_AVAILABLE:
            cc = Card()
            cc.setMinimumHeight(400)
            cl = QVBoxLayout(cc)
            
            s = QPieSeries()
            colors = [
                QColor("#42A5F5"), QColor("#66BB6A"), QColor("#FFA726"), QColor("#EF5350"), 
                QColor("#AB47BC"), QColor("#26C6DA"), QColor("#FF7043"), QColor("#8D6E63")
            ]
            
            total_budget = sum(tp["budget_breakdown"].values())
            keys_for_legend = [] 

            i = 0
            for k,v in tp["budget_breakdown"].items(): 
                slice_obj = s.append(k,v)
                slice_obj.setColor(colors[i % len(colors)])
                keys_for_legend.append(k)

                pct = (v / total_budget) * 100 if total_budget > 0 else 0
                slice_obj.setLabel(f"${v}")
                slice_obj.data_tooltip = f"{k}: ${v} ({pct:.1f}%)"
                
                if pct > 5:
                    slice_obj.setLabelVisible(True)
                else:
                    slice_obj.setLabelVisible(False)
                    
                slice_obj.hovered.connect(lambda state, slc=slice_obj: self.on_slice_hover(state, slc))
                i += 1
            
            if s.slices(): 
                s.slices()[0].setExploded(True)
                
            ch = QChart()
            ch.addSeries(s)
            ch.setTitle("Budget Breakdown")
            ch.setAnimationOptions(QChart.SeriesAnimations)
            ch.setTheme(QChart.ChartThemeLight)
            # FORCE Bottom alignment as requested
            ch.legend().setAlignment(Qt.AlignBottom)
            ch.legend().setFont(QFont("Arial", 10))
            
            markers = ch.legend().markers(s)
            for marker, key in zip(markers, keys_for_legend):
                marker.setLabel(key)

            cv = QChartView(ch)
            cv.setRenderHint(QPainter.Antialiasing)
            cl.addWidget(cv)
            self.res_l.addWidget(cc)

        # Day Cards
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