import base64
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, 
    QScrollArea, QFrame, QSplitter, QListWidget, QListWidgetItem, 
    QDialog, QPushButton, QStackedWidget, QDateEdit, QMessageBox, QFileDialog,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QByteArray, QTimer, QDate, QSize
from PySide6.QtGui import QPixmap, QImage, QPainter, QPainterPath, QColor

# --- Import Custom Components ---
from components import ScaleButton, ModernInput, FloatingParticle, GlassCard

# --- Helper UI Components ---
class ClickableImage(QLabel):
    clicked = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

class ImagePopup(QDialog):
    def __init__(self, pixmap):
        super().__init__()
        self.setWindowTitle("Trip Vibe")
        self.resize(800, 600)
        l = QVBoxLayout(self)
        lbl = QLabel()
        lbl.setPixmap(pixmap.scaled(780, 580, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        lbl.setAlignment(Qt.AlignCenter)
        l.addWidget(lbl)

class TripViewerView(QWidget):
    # Signals
    back_requested = Signal()
    pdf_requested = Signal()
    send_requested = Signal(str, str) # message, mode
    flight_search_requested = Signal(str, str, str) # origin, dest, date

    def __init__(self):
        super().__init__()
        self.image_placeholders = {}
        self.weather_labels = {}
        self.trip_widgets_map = {}
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background: #0F172A; font-family: 'Segoe UI';")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)

        # --- Top Bar ---
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(20, 20, 20, 10)
        
        self.btn_back = ScaleButton("⬅ Back", "#334155", "#1E293B")
        self.btn_back.setFixedSize(100, 40)
        self.btn_back.clicked.connect(self.back_requested.emit)
        
        self.btn_pdf = ScaleButton("📄 PDF", "#10B981", "#059669")
        self.btn_pdf.setFixedSize(100, 40)
        self.btn_pdf.clicked.connect(self.pdf_requested.emit)
        self.btn_pdf.setVisible(False)

        top_bar.addWidget(self.btn_back)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_pdf)
        main_layout.addLayout(top_bar)

        # --- Content Splitter ---
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet("QSplitter::handle { background: #334155; }")

        # Sidebar (TOC)
        toc_container = QWidget()
        toc_container.setFixedWidth(220)
        toc_container.setStyleSheet("background: rgba(30, 41, 59, 0.5); border-right: 1px solid #334155;")
        tl = QVBoxLayout(toc_container)
        lbl_ver = QLabel("📅 Versions")
        lbl_ver.setStyleSheet("color: #94A3B8; font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        tl.addWidget(lbl_ver)
        
        self.trip_list = QListWidget()
        self.trip_list.setStyleSheet("""
            QListWidget { background: transparent; border: none; color: white; }
            QListWidget::item { padding: 10px; border-radius: 8px; }
            QListWidget::item:selected { background: #3B82F6; }
            QListWidget::item:hover { background: #334155; }
        """)
        tl.addWidget(self.trip_list)
        splitter.addWidget(toc_container)

        # Main Feed
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.feed_cont = QWidget()
        self.feed_cont.setStyleSheet("background: transparent;")
        self.feed_layout = QVBoxLayout(self.feed_cont)
        self.feed_layout.setSpacing(20)
        self.feed_layout.setContentsMargins(30, 0, 30, 30)
        self.feed_layout.addStretch()
        
        self.scroll_area.setWidget(self.feed_cont)
        splitter.addWidget(self.scroll_area)
        
        main_layout.addWidget(splitter)

        # --- Chat Bar ---
        chat_container = QFrame()
        chat_container.setStyleSheet("background: #1E293B; border-top: 1px solid #334155;")
        chat_layout = QHBoxLayout(chat_container)
        chat_layout.setContentsMargins(20, 15, 20, 15)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["❓ Question", "🛠️ Refine Trip"])
        self.mode_combo.setFixedSize(140, 45)
        self.mode_combo.setStyleSheet("""
            QComboBox { background: #334155; color: white; border-radius: 10px; padding: 5px; }
            QComboBox::drop-down { border: none; }
        """)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask AI to change budget, dates, or details...")
        self.chat_input.setFixedHeight(45)
        self.chat_input.setStyleSheet("""
            QLineEdit { background: #0F172A; color: white; border: 1px solid #334155; border-radius: 10px; padding-left: 15px; }
            QLineEdit:focus { border: 1px solid #3B82F6; }
        """)
        self.chat_input.returnPressed.connect(self._on_send_click)

        self.btn_send = ScaleButton("➤", "#3B82F6", "#2563EB")
        self.btn_send.setFixedSize(50, 45)
        self.btn_send.clicked.connect(self._on_send_click)

        chat_layout.addWidget(self.mode_combo)
        chat_layout.addWidget(self.chat_input)
        chat_layout.addWidget(self.btn_send)
        
        main_layout.addWidget(chat_container)

    # --- Interaction Helpers ---
    def _on_send_click(self):
        text = self.chat_input.text().strip()
        if text:
            self.send_requested.emit(text, self.mode_combo.currentText())
            self.chat_input.clear()

    def add_bubble(self, text, is_user):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        # User = Blue, AI = White/Gray
        bg = "#3B82F6" if is_user else "#334155"
        color = "white"
        align = "margin-left: 60px;" if is_user else "margin-right: 60px;"
        
        lbl.setStyleSheet(f"""
            QLabel {{
                background-color: {bg}; color: {color};
                padding: 15px; border-radius: 15px;
                font-size: 14px; {align}
            }}
        """)
        self.feed_layout.insertWidget(self.feed_layout.count()-1, lbl)
        self.scroll_down()
        return lbl

    def update_bubble(self, lbl, text):
        lbl.setText(text)
        self.scroll_down()

    def render_trip_block(self, ver_id, title, plan_data):
        # 1. Sidebar Item
        list_item = QListWidgetItem(f"Ver {ver_id}")
        list_item.setToolTip(title)
        self.trip_list.addItem(list_item)

        # 2. Section Header
        lbl_head = QLabel(f"Version {ver_id}: {title}")
        lbl_head.setStyleSheet("font-size: 20px; font-weight: bold; color: #38BDF8; margin-top: 20px;")
        self.feed_layout.insertWidget(self.feed_layout.count()-1, lbl_head)
        self.trip_widgets_map[id(list_item)] = lbl_head

        # 3. Dashboard Row
        dash_layout = QHBoxLayout()
        dash_layout.setSpacing(15)

        # -- Image Card --
        img_card = GlassCard()
        img_card.setFixedSize(160, 160)
        il = QVBoxLayout(img_card); il.setAlignment(Qt.AlignCenter); il.setContentsMargins(0,0,0,0)
        ph_layout = QVBoxLayout(); ph_layout.setAlignment(Qt.AlignCenter)
        il.addLayout(ph_layout)
        self.image_placeholders[ver_id] = ph_layout
        dash_layout.addWidget(img_card)

        # -- Info Card --
        info_card = GlassCard()
        info_card.setFixedHeight(160)
        il2 = QVBoxLayout(info_card)
        il2.addWidget(QLabel(f"✨ {plan_data.get('analyzed_vibe', 'Trip').upper()} VIBE", styleSheet="color: #64748B; font-weight: bold; font-size: 12px; border:none; background:transparent;"))
        summary = QLabel(plan_data.get("summary", ""))
        summary.setWordWrap(True)
        summary.setStyleSheet("color: #1E293B; font-size: 14px; border:none; background:transparent;")
        il2.addWidget(summary)
        il2.addStretch()
        
        # Weather slot
        lbl_weather = QLabel("--")
        lbl_weather.setStyleSheet("color: #0369A1; font-weight: bold; font-size: 16px; border:none; background:transparent;")
        self.weather_labels[ver_id] = lbl_weather
        il2.addWidget(lbl_weather)
        dash_layout.addWidget(info_card)

        self.feed_layout.insertLayout(self.feed_layout.count()-1, dash_layout)

        # 4. Itinerary
        for day in plan_data.get("itinerary", []):
            day_card = GlassCard()
            dl = QVBoxLayout(day_card)
            dl.addWidget(QLabel(f"Day {day['day']}: {day['title']}", styleSheet="font-weight: bold; color: #1E293B; font-size: 16px; border:none; background:transparent;"))
            for act in day.get("activities", []):
                dl.addWidget(QLabel(f"• {act}", styleSheet="color: #475569; margin-left: 10px; border:none; background:transparent;"))
            self.feed_layout.insertWidget(self.feed_layout.count()-1, day_card)

        self.scroll_down()

    def set_image(self, ver_id, b64_data):
        layout = self.image_placeholders.get(ver_id)
        if not layout: return
        # Clear previous
        while layout.count(): item = layout.takeAt(0); item.widget().deleteLater() if item.widget() else None
        
        if not b64_data: return

        try:
            data = base64.b64decode(b64_data)
            pix = QPixmap.fromImage(QImage.fromData(QByteArray(data)))
            
            # Round corners logic
            size = 140
            rounded = QPixmap(size, size)
            rounded.fill(Qt.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing, True)
            path = QPainterPath()
            path.addRoundedRect(0, 0, size, size, 15, 15)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pix.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            painter.end()

            lbl = ClickableImage()
            lbl.setPixmap(rounded)
            lbl.clicked.connect(lambda: ImagePopup(pix).exec())
            layout.addWidget(lbl)
        except Exception as e:
            print(f"Img Error: {e}")

    def update_weather(self, ver_id, text):
        if ver_id in self.weather_labels:
            self.weather_labels[ver_id].setText(text)

    def scroll_down(self):
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))

    def reset_view(self):
        self.trip_list.clear()
        self.image_placeholders = {}
        self.weather_labels = {}
        # Clear feed (keep stretch)
        while self.feed_layout.count() > 1:
            item = self.feed_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout(): 
                # Recursive clear logic needed here properly
                item.layout().deleteLater()