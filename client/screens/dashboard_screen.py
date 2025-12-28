import json
import base64
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                               QLineEdit, QSpinBox, QComboBox, 
                               QScrollArea, QMessageBox, QFrame, QSplitter, QToolTip,
                               QStackedWidget, QTextEdit, QPlainTextEdit, QTabWidget)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QByteArray
from PySide6.QtGui import QPainter, QFont, QColor, QCursor, QPixmap, QImage

try:
    from PySide6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False

from client.components.custom_widgets import Card
from client.logic.workers import TripWorker

# --- Central Stylesheet ---
STYLESHEET = """
    QMainWindow { background-color: #f0f2f5; }
    QWidget { font-family: 'Segoe UI', Arial, sans-serif; }
    
    QLabel { color: #263238; }
    QLabel#Header { font-size: 26px; font-weight: 900; color: #1565c0; }
    QLabel#SectionTitle { font-size: 18px; font-weight: bold; color: #37474f; margin-bottom: 5px; }
    QLabel#InputLabel { font-size: 14px; font-weight: 600; color: #546e7a; margin-top: 5px; }

    QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox { 
        background-color: #ffffff; color: #333333; border: 1px solid #cfd8dc; border-radius: 6px; padding: 8px 10px; font-size: 14px;
    }
    QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus { border: 2px solid #2196f3; }

    QPushButton#PrimaryBtn {
        background-color: #1565c0; color: white; border: none; border-radius: 8px; padding: 12px; font-weight: bold; font-size: 16px;
    }
    QPushButton#PrimaryBtn:hover { background-color: #0d47a1; }
    QPushButton#PrimaryBtn:disabled { background-color: #b0bec5; color: #eceff1; }

    QPushButton#SecondaryBtn {
        background-color: white; color: #455a64; border: 1px solid #b0bec5; border-radius: 6px; padding: 6px 12px; font-weight: 600;
    }
    QPushButton#SecondaryBtn:hover { background-color: #f5f5f5; border: 1px solid #78909c; }
    
    QFrame#Card { background-color: white; border-radius: 12px; border: 1px solid #e0e0e0; }

    /* --- Tabs Styling --- */
    QTabWidget::pane { 
        border: 1px solid #e0e0e0; 
        background: #f8f9fa; 
        border-radius: 8px;
    }
    QTabBar::tab {
        background: #eceff1;
        border: 1px solid #cfd8dc;
        padding: 8px 16px;
        margin-right: 4px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        font-weight: bold;
        color: #546e7a;
    }
    QTabBar::tab:selected {
        background: #ffffff;
        border-bottom-color: #ffffff;
        color: #1565c0;
        border-top: 2px solid #1565c0;
    }
    QTabBar::tab:hover {
        background: #ffffff;
    }
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
            response = self.api.post("/generate_image", {
                "destination": self.destination,
                "interest": self.interest
            })
            
            if response and "image_base64" in response:
                self.finished_signal.emit(response["image_base64"])
            else:
                self.finished_signal.emit(None)
        except Exception as e:
            print(f"Image Worker Error: {e}")
            self.finished_signal.emit(None)


class DashboardScreen(QWidget):
    def __init__(self, switch_cb, api):
        super().__init__()
        self.switch_cb, self.api = switch_cb, api
        self.curr_user = None
        
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
        
        self.current_trip_context = "" 
        self.trip_counter = 0

    def create_input_panel(self):
        layout = QVBoxLayout(self.left_panel)
        layout.setContentsMargins(0,0,10,0)

        self.left_stack = QStackedWidget()
        
        self.page_form = QWidget()
        self.setup_form_page(self.page_form)
        self.left_stack.addWidget(self.page_form)
        
        self.page_chat = QWidget()
        self.setup_chat_page(self.page_chat)
        self.left_stack.addWidget(self.page_chat)
        
        layout.addWidget(self.left_stack)

    def setup_form_page(self, parent_widget):
        outer = QVBoxLayout(parent_widget)
        outer.setContentsMargins(0,0,0,0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        card = QFrame()
        card.setObjectName("Card")
        cl = QVBoxLayout(card)
        cl.setSpacing(12)
        cl.setContentsMargins(20,20,20,20)

        cl.addWidget(QLabel("Plan New Trip ✈️", objectName="SectionTitle"))
        
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
        
        # Interest
        cl.addWidget(QLabel("Interest / Vibe:", objectName="InputLabel"))
        self.interest = QPlainTextEdit()
        self.interest.setPlaceholderText("e.g. 'I want relax & good food. Maybe some museums.'")
        self.interest.setFixedHeight(70) 
        cl.addWidget(self.interest)

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
        self.btn_go = QPushButton("✨ Generate Trip & Image")
        self.btn_go.setObjectName("PrimaryBtn")
        self.btn_go.setMinimumHeight(45)
        self.btn_go.setCursor(Qt.PointingHandCursor)
        self.btn_go.clicked.connect(self.go)
        cl.addWidget(self.btn_go)
        cl.addStretch()
        
        scroll.setWidget(card)
        outer.addWidget(scroll)

    def setup_chat_page(self, parent_widget):
        cl = QVBoxLayout(parent_widget)
        cl.setContentsMargins(0,0,0,0)
        
        card = QFrame()
        card.setObjectName("Card")
        l = QVBoxLayout(card)
        l.setContentsMargins(15,15,15,15)
        
        l.addWidget(QLabel("💬 Trip Assistant", objectName="SectionTitle"))
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("border: none; background: #fafafa; font-size: 14px; color: #333333;")
        l.addWidget(self.chat_display)
        
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
        
        btn_reset = QPushButton("↺ Start Over")
        btn_reset.setObjectName("SecondaryBtn")
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.clicked.connect(self.reset_planning)
        l.addWidget(btn_reset)
        
        cl.addWidget(card)

    def create_results_panel(self):
        l = QVBoxLayout(self.right_panel)
        l.setContentsMargins(5,0,0,0)
        
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True) 
        self.tabs.tabCloseRequested.connect(self.close_tab) 
        
        self.welcome_tab = QWidget()
        wl = QVBoxLayout(self.welcome_tab)
        
        ph = QLabel("👈 Fill the form and click Generate\nEach new plan will appear in a new tab!")
        ph.setAlignment(Qt.AlignCenter)
        ph.setStyleSheet("color: #90a4ae; font-size: 18px; font-weight: bold;")
        wl.addWidget(ph)
        
        self.tabs.addTab(self.welcome_tab, "Start Here")
        l.addWidget(self.tabs)

    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)

    def start_new_trip_tab(self):
        self.trip_counter += 1
        
        new_tab = QWidget()
        new_layout = QVBoxLayout(new_tab)
        new_layout.setContentsMargins(0,0,0,0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background-color: #f8f9fa; border: none;")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(30,30,30,30)
        
        # הוספת הודעת טעינה בתוך הטאב החדש
        loader_lbl = QLabel("🤖 AI is planning your trip...")
        loader_lbl.setAlignment(Qt.AlignCenter)
        loader_lbl.setStyleSheet("color: #1565c0; font-size: 16px;")
        loader_lbl.setObjectName("MainLoader")
        content_layout.addWidget(loader_lbl)
        content_layout.addStretch()
        
        scroll.setWidget(content)
        new_layout.addWidget(scroll)
        
        tab_index = self.tabs.addTab(new_tab, f"Trip {self.trip_counter} ⏳")
        self.tabs.setCurrentIndex(tab_index)
        
        return content_layout 

    def go(self):
        if not self.dest.text() or not self.origin.text():
            QMessageBox.warning(self, "Missing Info", "Origin & Destination required")
            return
            
        self.left_stack.setCurrentIndex(1)
        self.chat_display.clear()
        self.append_chat("System", "Generating trip plan and visuals... 🤖🎨")
        
        self.current_trip_context = self.interest.toPlainText()
        self.btn_go.setText("Generating...")
        
        self.start_new_trip_tab()

        # 1. תכנון הטיול
        self.call_worker()
        
        # 2. יצירת התמונה (הראשונית)
        self.img_worker = ImageWorker(self.api, self.dest.text(), self.interest.toPlainText())
        self.img_worker.finished_signal.connect(self.show_trip_image)
        self.img_worker.start()

    def send_chat(self):
        msg = self.chat_input.text().strip()
        if not msg: return
        
        self.chat_input.clear()
        self.append_chat("You", msg)
        self.append_chat("System", "Refining plan... ⏳")
        
        self.start_new_trip_tab()
        
        # עדכון ההקשר עם הבקשה החדשה
        self.current_trip_context += f"\n[User Modification]: {msg}"
        
        # 1. הפעלת ה-AI לטיול
        self.call_worker()

        # 2. --- השינוי הגדול: הפעלת יצירת תמונה גם בצ'אט ---
        # אנחנו שולחים את ה-Context המעודכן (שכולל את הבקשה החדשה שלך)
        # כדי שהתמונה תשקף את השינויים (למשל "Add Snow")
        self.img_worker = ImageWorker(self.api, self.dest.text(), self.current_trip_context)
        self.img_worker.finished_signal.connect(self.show_trip_image)
        self.img_worker.start()

    def call_worker(self):
        self.worker = TripWorker(
            self.api, self.curr_user, 
            self.dest.text(), self.origin.text(), self.stops.text(),
            self.budg.value(), self.curr.currentText(),
            self.current_trip_context, 
            self.days.value()
        )
        self.worker.finished_signal.connect(self.show_res)
        self.worker.start()

    def reset_planning(self):
        self.left_stack.setCurrentIndex(0) 
        self.chat_display.clear()
        self.current_trip_context = ""
        self.btn_go.setText("✨ Generate Trip & Image")
        self.trip_counter = 0
        
        self.tabs.clear()
        self.create_results_panel() 

    def append_chat(self, sender, text):
        color = "#1565c0" if sender == "System" else "#2e7d32"
        self.chat_display.append(f"<b style='color:{color}'>{sender}:</b> {text}")

    # --- הצגת תמונה ---
    def show_trip_image(self, base64_str):
        current_widget = self.tabs.currentWidget()
        if not current_widget: return
        
        scroll_area = current_widget.findChild(QScrollArea)
        if not scroll_area: return
        
        content_widget = scroll_area.widget()
        layout = content_widget.layout()

        # ניקוי הודעות טעינה
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            widget = item.widget()
            if widget and isinstance(widget, QLabel):
                if "AI is painting" in widget.text():
                    widget.setParent(None)

        if not base64_str:
            err = QLabel("⚠️ Image generation timed out (Server busy).")
            err.setStyleSheet("color: #ef5350; font-style: italic; margin-bottom: 10px;")
            layout.insertWidget(0, err)
            return 

        try:
            img_data = base64.b64decode(base64_str)
            image = QImage.fromData(QByteArray(img_data))
            pixmap = QPixmap.fromImage(image)
            
            lbl_img = QLabel()
            lbl_img.setPixmap(pixmap.scaledToWidth(600, Qt.SmoothTransformation))
            lbl_img.setAlignment(Qt.AlignCenter)
            lbl_img.setStyleSheet("border: 4px solid white; border-radius: 12px; margin-bottom: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1);")
            
            layout.insertWidget(0, lbl_img)
        except Exception as e:
            print(f"Error displaying image: {e}")

    # --- Tooltip ---
    def on_slice_hover(self, state, slice_obj):
        if state:
            if hasattr(slice_obj, 'data_tooltip'):
                QToolTip.showText(QCursor.pos(), slice_obj.data_tooltip)
        else:
            QToolTip.hideText()

    def show_res(self, data):
        self.btn_go.setText("✨ Generate Trip & Image")
        
        current_idx = self.tabs.currentIndex()
        self.tabs.setTabText(current_idx, f"Trip {self.trip_counter}")

        current_widget = self.tabs.currentWidget()
        if not current_widget: return
        scroll_area = current_widget.findChild(QScrollArea)
        content_widget = scroll_area.widget()
        layout = content_widget.layout()

        # הסרת "AI is planning"
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            widget = item.widget()
            if widget and isinstance(widget, QLabel) and widget.objectName() == "MainLoader":
                widget.setParent(None)

        if self.left_stack.currentIndex() == 1:
             self.append_chat("System", "Plan updated! ✅")
        
        if "error" in data:
            err = QLabel(f"Error: {data['error']}")
            err.setStyleSheet("color: red; font-size: 16px;")
            layout.addWidget(err)
            layout.addStretch()
            return
        
        # הודעת טעינה לתמונה
        img_loader = QLabel("🎨 AI is painting your scene... (approx 20s)")
        img_loader.setStyleSheet("color: #1565c0; font-style: italic; font-weight: bold; margin-bottom: 10px;")
        layout.insertWidget(0, img_loader)

        tp = data.get("trip_plan", {})
        if isinstance(tp, str): tp = json.loads(tp)
        
        c = Card()
        l = QVBoxLayout(c)
        l.addWidget(QLabel(f"✈️ Trip to {self.dest.text()}", styleSheet="font-size: 26px; font-weight: 900; color: #1565c0;"))
        l.addWidget(QLabel(tp.get("summary", ""), wordWrap=True, styleSheet="font-size: 16px; margin-top: 15px; line-height: 1.5; color: #333;"))
        layout.addWidget(c)
        
        if "budget_breakdown" in tp and CHARTS_AVAILABLE:
            cc = Card()
            cc.setMinimumHeight(400)
            cl = QVBoxLayout(cc)
            s = QPieSeries()
            colors = [QColor("#42A5F5"), QColor("#66BB6A"), QColor("#FFA726"), QColor("#EF5350"), QColor("#AB47BC")]
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
                slice_obj.setLabelVisible(pct > 5)
                slice_obj.hovered.connect(lambda state, slc=slice_obj: self.on_slice_hover(state, slc))
                i += 1
            if s.slices(): s.slices()[0].setExploded(True)
            ch = QChart()
            ch.addSeries(s)
            ch.setTitle("Budget Breakdown")
            ch.legend().setAlignment(Qt.AlignBottom)
            ch.legend().setFont(QFont("Arial", 10))
            markers = ch.legend().markers(s)
            for marker, key in zip(markers, keys_for_legend): marker.setLabel(key)
            cv = QChartView(ch)
            cv.setRenderHint(QPainter.Antialiasing)
            cl.addWidget(cv)
            layout.addWidget(cc)

        for d in tp.get("itinerary", []):
            dc = Card()
            dl = QVBoxLayout(dc)
            dl.addWidget(QLabel(f"Day {d.get('day')}: {d.get('title')}", styleSheet="font-size: 18px; font-weight: bold; color: #37474f;"))
            dl.addSpacing(5)
            for a in d.get("activities", []): 
                dl.addWidget(QLabel(f"• {a}", wordWrap=True, styleSheet="font-size: 14px; margin-bottom: 2px;"))
            layout.addWidget(dc)
            
        layout.addStretch()

    def set_user(self, u):
        self.curr_user = u
        self.lbl_welcome.setText(f"Welcome, {u} 👋")