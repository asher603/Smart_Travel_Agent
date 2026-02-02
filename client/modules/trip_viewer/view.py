"""
Trip Viewer View - Premium Travel Experience UI
Styled to match the Smart Travel Agent design system
"""
import base64
import os
import re
import json
import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QScrollArea, QFrame, QSplitter, 
    QListWidget, QListWidgetItem, QDialog, QMessageBox, QFileDialog,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QByteArray, QTimer
from PySide6.QtGui import QPixmap, QColor

# 🛡️ Security
from core.security import validate_and_protect

from .workers import (
    ImageWorker, ChatWorker, StateSaverWorker, 
    WeatherWorker, FlightWorker, BudgetWorker, RefineWorker
)

# Import custom components
from components.floating_particle import FloatingParticle
from components.modern_input import ModernInput
from components.scale_button import ScaleButton
from components.glass_card import GlassCard

try:
    from utils.pdf_generator import generate_trip_pdf
except ImportError:
    generate_trip_pdf = None

try:
    from components import BudgetPieChart
except ImportError as e:
    BudgetPieChart = None
    print(f"❌ Budget Pie Chart not found: {e}")

# ============================================================================
#                           HELPER CLASSES
# ============================================================================

class ClickableImage(QLabel):
    """Image label with click signal"""
    clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        
    def mousePressEvent(self, e):
        self.clicked.emit()
        super().mousePressEvent(e)


class ImagePopup(QDialog):
    """Modern fullscreen image viewer"""
    def __init__(self, pixmap):
        super().__init__()
        self.setWindowTitle("Trip Image")
        self.setStyleSheet("""
            QDialog {
                background: rgba(15, 23, 42, 0.95);
            }
        """)
        self.resize(900, 700)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Image
        lbl = QLabel()
        lbl.setPixmap(pixmap.scaled(860, 620, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(lbl)
        
        # Close button
        btn_close = QPushButton("✕ Close")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setFixedHeight(45)
        btn_close.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #2563EB);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #3B82F6);
            }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


class ChatBubble(QFrame):
    """Modern chat message bubble"""
    def __init__(self, text, is_user=False):
        super().__init__()
        self.is_user = is_user
        
        if is_user:
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #2563EB);
                    border-radius: 16px;
                    border-top-right-radius: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 16px;
                    border-top-left-radius: 4px;
                    border: 1px solid rgba(226, 232, 240, 0.5);
                }
            """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.label.setStyleSheet(f"""
            QLabel {{
                color: {'white' if is_user else '#1E293B'};
                font-size: 14px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(self.label)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)


# ============================================================================
#                           MAIN VIEW CLASS
# ============================================================================
class TripViewerView(QWidget):
    """Premium Trip Viewer with modern dark theme"""
    back_signal = Signal()
    state_updated_signal = Signal(list)

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
        self.current_plan_data = {}
        self.current_context = ""
        self.current_image_b64 = None  # Store current trip image
        self.current_weather = None  # Store current weather

        self.setup_ui()
        self.create_particles()

    def create_particles(self):
        """Create floating background particles"""
        for _ in range(15):
            size = random.randint(5, 18)
            x = random.randint(0, 1200)
            y = random.randint(0, 900)
            p = FloatingParticle(self, x, y, size)
            p.lower()

    def set_api(self, api_service):
        self.api = api_service

    def setup_ui(self):
        # Main dark background
        self.setStyleSheet("""
            QWidget { 
                background: #0F172A; 
                font-family: 'Segoe UI'; 
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ==================== HEADER ====================
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #3B82F6, stop:1 #8B5CF6);
                border: none;
            }
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 0, 30, 0)
        
        # Back button
        btn_back = QPushButton("← Back")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setFixedSize(100, 40)
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.15);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 10px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.25);
            }
        """)
        btn_back.clicked.connect(self.go_back)
        header_layout.addWidget(btn_back)
        
        # Title
        title = QLabel("🗺️ Trip Planner")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 26px;
                font-weight: 800;
                background: transparent;
                border: none;
            }
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # PDF Download button
        self.btn_pdf = QPushButton("📄 Export PDF")
        self.btn_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_pdf.setFixedSize(130, 40)
        self.btn_pdf.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.95);
                color: #3B82F6;
                border: none;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: white;
            }
        """)
        self.btn_pdf.clicked.connect(self.save_pdf)
        self.btn_pdf.setVisible(False)
        header_layout.addWidget(self.btn_pdf)
        
        main_layout.addWidget(header)
        
        # ==================== CONTENT AREA ====================
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(25, 25, 25, 25)
        content_layout.setSpacing(25)
        
        # ---------- LEFT SIDEBAR: Versions ----------
        sidebar = GlassCard()
        sidebar.setFixedWidth(260)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 24, 20, 20)
        sidebar_layout.setSpacing(16)
        
        sidebar_title = QLabel("📅 Trip Versions")
        sidebar_title.setStyleSheet("""
            QLabel {
                color: #1E293B;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        sidebar_layout.addWidget(sidebar_title)
        
        self.trip_list = QListWidget()
        self.trip_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(248, 250, 252, 0.8);
                border: 1px solid rgba(226, 232, 240, 0.5);
                border-radius: 12px;
                padding: 8px;
                font-size: 13px;
                color: #334155;
            }
            QListWidget::item {
                padding: 12px 10px;
                border-radius: 8px;
                margin: 2px 0;
            }
            QListWidget::item:selected {
                background-color: rgba(59, 130, 246, 0.15);
                color: #3B82F6;
                font-weight: bold;
            }
            QListWidget::item:hover {
                background-color: rgba(59, 130, 246, 0.08);
            }
        """)
        self.trip_list.itemClicked.connect(self.scroll_to_item)
        sidebar_layout.addWidget(self.trip_list)
        
        content_layout.addWidget(sidebar)
        
        # ---------- RIGHT: Main Feed ----------
        feed_container = QWidget()
        feed_container.setStyleSheet("background: transparent;")
        feed_layout_outer = QVBoxLayout(feed_container)
        feed_layout_outer.setContentsMargins(0, 0, 0, 0)
        feed_layout_outer.setSpacing(20)
        
        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background-color: rgba(255, 255, 255, 0.1);
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(59, 130, 246, 0.5);
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(59, 130, 246, 0.8);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        self.feed_cont = QWidget()
        self.feed_cont.setStyleSheet("background: transparent;")
        self.feed_layout = QVBoxLayout(self.feed_cont)
        self.feed_layout.setSpacing(20)
        self.feed_layout.setContentsMargins(0, 0, 10, 20)
        self.feed_layout.addStretch()
        
        self.scroll_area.setWidget(self.feed_cont)
        feed_layout_outer.addWidget(self.scroll_area)
        
        # ==================== CHAT INPUT AREA ====================
        chat_container = GlassCard()
        chat_container.setFixedHeight(130)
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(24, 20, 24, 20)
        chat_layout.setSpacing(14)
        
        # Mode & Model selectors row
        selectors_row = QHBoxLayout()
        selectors_row.setSpacing(16)
        
        mode_label = QLabel("Mode:")
        mode_label.setStyleSheet("""
            QLabel {
                color: #64748B;
                font-size: 13px;
                font-weight: 600;
                background: transparent;
                border: none;
            }
        """)
        selectors_row.addWidget(mode_label)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["❓ Question", "🛠️ Fix / New Trip"])
        self.mode_combo.setCursor(Qt.PointingHandCursor)
        self.mode_combo.setFixedHeight(36)
        self.mode_combo.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                border: 2px solid #E2E8F0;
                border-radius: 8px;
                padding: 0 12px;
                font-size: 13px;
                color: #1E293B;
                min-width: 160px;
            }
            QComboBox:hover {
                border-color: #3B82F6;
                background-color: #FFFFFF;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border: none;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #64748B;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                border: 2px solid #E2E8F0;
                border-radius: 8px;
                selection-background-color: #EFF6FF;
                selection-color: #1D4ED8;
                color: #1E293B;
                padding: 5px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                min-height: 32px;
                padding: 5px 10px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #F1F5F9;
            }
        """)
        selectors_row.addWidget(self.mode_combo)
        
        model_label = QLabel("AI:")
        model_label.setStyleSheet("""
            QLabel {
                color: #64748B;
                font-size: 13px;
                font-weight: 600;
                background: transparent;
                border: none;
                margin-left: 10px;
            }
        """)
        selectors_row.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["Gemini", "Groq", "Ollama"])
        self.model_combo.setToolTip("Select AI Model")
        self.model_combo.setCursor(Qt.PointingHandCursor)
        self.model_combo.setFixedHeight(36)
        self.model_combo.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                border: 2px solid #E2E8F0;
                border-radius: 8px;
                padding: 0 12px;
                font-size: 13px;
                color: #1E293B;
                min-width: 110px;
            }
            QComboBox:hover {
                border-color: #8B5CF6;
                background-color: #FFFFFF;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border: none;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #64748B;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                border: 2px solid #E2E8F0;
                border-radius: 8px;
                selection-background-color: #F3E8FF;
                selection-color: #7C3AED;
                color: #1E293B;
                padding: 5px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                min-height: 32px;
                padding: 5px 10px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #F1F5F9;
            }
        """)
        selectors_row.addWidget(self.model_combo)
        selectors_row.addStretch()
        
        chat_layout.addLayout(selectors_row)
        
        # Input + Send button row
        input_row = QHBoxLayout()
        input_row.setSpacing(12)
        
        self.chat_input = ModernInput("Ask a question or request changes...", icon_char="💬")
        self.chat_input.returnPressed.connect(self.on_send)
        input_row.addWidget(self.chat_input)
        
        btn_send = ScaleButton("Send →", "#3B82F6", "#8B5CF6")
        btn_send.setFixedWidth(110)
        btn_send.clicked.connect(self.on_send)
        input_row.addWidget(btn_send)
        
        chat_layout.addLayout(input_row)
        
        feed_layout_outer.addWidget(chat_container)
        content_layout.addWidget(feed_container, 1)
        
        main_layout.addWidget(content_widget)

    # ============================================================================
    #                           WORKER MANAGEMENT
    # ============================================================================

    def start_worker(self, worker):
        """Start a background worker thread"""
        self.active_workers.append(worker)
        worker.finished.connect(lambda: self.cleanup_worker(worker))
        worker.start()

    def cleanup_worker(self, worker):
        """Clean up finished worker"""
        if worker in self.active_workers:
            self.active_workers.remove(worker)
        worker.deleteLater()

    # ============================================================================
    #                           NAVIGATION
    # ============================================================================

    def go_back(self):
        """Navigate back to previous screen"""
        if not self.is_loading_mode:
            self.save_state_to_server()
        self.back_signal.emit()

    # ============================================================================
    #                           UI RESET & CLEANUP
    # ============================================================================

    def clear_layout(self, layout):
        """Recursively clear a layout"""
        if not layout:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def reset_ui(self):
        """Reset UI to initial state"""
        # Stop all workers
        for w in self.active_workers:
            try:
                w.blockSignals(True)
                if w.isRunning():
                    w.quit()
                    w.wait(50)
            except:
                pass
        self.active_workers.clear()

        # Reset state
        self.trip_list.clear()
        self.chat_history_state = []
        self.trip_counter = 0
        self.trip_widgets_map = {}
        self.image_placeholders = {} 
        self.weather_labels = {}
        self.current_active_ver_id = None

        # Clear feed layout
        if self.feed_layout:
            self.clear_layout(self.feed_layout)
            self.feed_layout.addStretch()

    # ============================================================================
    #                           TRIP INITIALIZATION
    # ============================================================================

    def init_new_trip(self, trip_response, username):
        """Initialize view for a new trip"""
        self.is_loading_mode = False
        self.reset_ui()
        self.username = username
        self.trip_id = trip_response.get("trip_id")
        plan = trip_response
        dest = plan.get("destination", "Unknown")
        self.current_plan_data = plan
        self.current_context = json.dumps(plan, default=str, indent=2)
        self.btn_pdf.setVisible(True)
        
        self.render_trip_block("Initial Plan", plan, is_new=True)
        self.trigger_image_generation(dest, "travel", self.trip_counter)
        self.fetch_weather(dest)

    def load_existing_trip(self, full_data):
        """Load an existing trip from history"""
        self.is_loading_mode = True 
        self.reset_ui()
        
        self.trip_id = full_data.get("id") or full_data.get("_id") or full_data.get("trip_id")
        self.username = full_data.get("username", "")
        dest = full_data.get("destination", "")
        self.current_context = f"Dest: {dest}"
        
        self.chat_history_state = full_data.get("chat_history", [])
        history = self.chat_history_state
        
        if not history and "destination" in full_data:
            self.render_trip_block("Saved Plan", full_data, save=False)
            self.current_plan_data = full_data
        else:
            for item in history:
                t = item.get("type")
                c = item.get("content")
                if t == "text": 
                    self.add_bubble(c, item.get("is_user"), save=False)
                elif t == "plan": 
                    self.current_plan_data = c["plan"]
                    self.render_trip_block(c["title"], c["plan"], save=False)
                elif t == "image": 
                    self.render_image_in_placeholder(c, self.trip_counter, save=False)
        
        if hasattr(self, 'current_plan_data') and self.current_plan_data:
            self.current_context = json.dumps(self.current_plan_data, default=str, indent=2)
        else:
            self.current_context = json.dumps(full_data, default=str, indent=2)

        self.is_loading_mode = False
        if dest:
            self.fetch_weather(dest)
        if hasattr(self, 'current_plan_data'):
            self.btn_pdf.setVisible(True)
        
    # ============================================================================
    #                           TRIP BLOCK RENDERING
    # ============================================================================

    def render_trip_block(self, title, plan_data, is_new=False, save=True):
        """Render a complete trip block with all sections"""
        self.trip_counter += 1
        ver_id = self.trip_counter
        self.current_active_ver_id = ver_id 
        
        # Add to sidebar list
        item = QListWidgetItem(f"✦ Ver {ver_id} - {title}")
        self.trip_list.addItem(item)
        
        # Version header
        version_header = QLabel(f"🌟 Version {ver_id}: {title}")
        version_header.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
                color: white;
                margin-top: 10px;
                background: transparent;
                border: none;
            }
        """)
        self.feed_layout.insertWidget(self.feed_layout.count()-1, version_header)
        self.trip_widgets_map[id(item)] = version_header
        
        # ==================== ROW 1: DASHBOARD CARDS ====================
        row1 = QHBoxLayout()
        row1.setSpacing(16)
        CARD_HEIGHT = 180

        # 1. Image Card
        img_card = GlassCard()
        img_card.setFixedSize(CARD_HEIGHT, CARD_HEIGHT)
        img_layout = QVBoxLayout(img_card)
        img_layout.setContentsMargins(8, 8, 8, 8)
        
        # Loading placeholder
        loading_lbl = QLabel("🎨")
        loading_lbl.setAlignment(Qt.AlignCenter)
        loading_lbl.setStyleSheet("""
            QLabel {
                font-size: 48px;
                background: transparent;
                border: none;
            }
        """)
        img_layout.addWidget(loading_lbl)
        
        self.image_placeholders[ver_id] = img_layout 
        row1.addWidget(img_card)

        # 2. Trip Vibe Card
        vibe_card = GlassCard()
        vibe_card.setFixedHeight(CARD_HEIGHT)
        vc_layout = QVBoxLayout(vibe_card)
        vc_layout.setContentsMargins(20, 16, 20, 16)
        vc_layout.setSpacing(10)
        
        vibe_header = QLabel("✨ TRIP VIBE")
        vibe_header.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #64748B;
                letter-spacing: 0.5px;
                background: transparent;
                border: none;
            }
        """)
        vc_layout.addWidget(vibe_header)
        
        vibe_text = plan_data.get("summary", "An amazing adventure awaits you!")
        lbl_vibe = QLabel(vibe_text)
        lbl_vibe.setWordWrap(True) 
        lbl_vibe.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #8B5CF6;
                font-weight: 500;
                line-height: 1.4;
                background: transparent;
                border: none;
            }
        """)
        lbl_vibe.setAlignment(Qt.AlignTop)
        vc_layout.addWidget(lbl_vibe)
        vc_layout.addStretch()
        row1.addWidget(vibe_card, 3)

        # 3. Weather Card
        weather_card = GlassCard()
        weather_card.setFixedHeight(CARD_HEIGHT)
        weather_card.setFixedWidth(160)
        wc_layout = QVBoxLayout(weather_card)
        wc_layout.setContentsMargins(16, 16, 16, 16)
        wc_layout.setSpacing(6)
        
        dest_name = plan_data.get("destination", "").upper()
        dest_lbl = QLabel(dest_name[:15] + "..." if len(dest_name) > 15 else dest_name)
        dest_lbl.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: bold;
                color: #64748B;
                letter-spacing: 0.5px;
                background: transparent;
                border: none;
            }
        """)
        wc_layout.addWidget(dest_lbl)
        
        lbl_weather = QLabel("⏳")
        self.weather_labels[ver_id] = lbl_weather
        lbl_weather.setStyleSheet("""
            QLabel {
                font-size: 28px;
                color: #0EA5E9;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        lbl_weather.setAlignment(Qt.AlignCenter)
        wc_layout.addWidget(lbl_weather)
        
        forecast_lbl = QLabel("Current Weather")
        forecast_lbl.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #94A3B8;
                background: transparent;
                border: none;
            }
        """)
        forecast_lbl.setAlignment(Qt.AlignCenter)
        wc_layout.addWidget(forecast_lbl)
        wc_layout.addStretch()
        row1.addWidget(weather_card)

        self.feed_layout.insertLayout(self.feed_layout.count()-1, row1)

        # ==================== ROW 2: FLIGHTS & BUDGET ====================
        row2 = QHBoxLayout()
        row2.setSpacing(16)
        ROW2_HEIGHT = 240

        # 1. Flights Card
        flight_card = GlassCard()
        flight_card.setFixedHeight(ROW2_HEIGHT)
        fc_layout = QVBoxLayout(flight_card)
        fc_layout.setContentsMargins(20, 18, 20, 18)
        fc_layout.setSpacing(12)
        
        flight_header = QLabel("✈️ Flight Search")
        flight_header.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 15px;
                color: #1E293B;
                background: transparent;
                border: none;
            }
        """)
        fc_layout.addWidget(flight_header)
        
        origin_city = plan_data.get("origin", "Tel Aviv")
        btn_search_flights = QPushButton(f"🔎 Search from {origin_city}")
        btn_search_flights.setCursor(Qt.PointingHandCursor)
        btn_search_flights.setFixedHeight(40)
        btn_search_flights.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #EFF6FF, stop:1 #DBEAFE);
                color: #1D4ED8;
                border: 1px solid #BFDBFE;
                border-radius: 10px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #DBEAFE, stop:1 #BFDBFE);
            }
        """)
        fc_layout.addWidget(btn_search_flights)
        
        flight_list = QListWidget()
        flight_list.setStyleSheet("""
            QListWidget {
                background: rgba(248, 250, 252, 0.8);
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                font-size: 12px;
                color: #475569;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #F1F5F9;
            }
            QListWidget::item:selected {
                background: #EFF6FF;
                color: #1D4ED8;
            }
        """)
        fc_layout.addWidget(flight_list)

        def do_flight_search():
            flight_list.clear()
            flight_list.addItem("🔄 Searching flights...")
            w = FlightWorker(self.api, origin_city, plan_data.get("destination"), plan_data.get("start_date"))
            w.finished_signal.connect(lambda res: update_flights(res, flight_list))
            self.start_worker(w)

        def update_flights(res, list_w):
            list_w.clear()
            if not res:
                list_w.addItem("❌ No flights found")
                return
            for f in res:
                list_w.addItem(f"🛫 {f['carrier']} | 💰 {f['price']} | {f['stops']}")

        btn_search_flights.clicked.connect(do_flight_search)
        row2.addWidget(flight_card, 1)

        # 2. Budget Card
        budget_card = GlassCard()
        budget_card.setFixedHeight(ROW2_HEIGHT)
        bc_layout = QVBoxLayout(budget_card)
        bc_layout.setContentsMargins(20, 18, 20, 18)
        bc_layout.setSpacing(10)
        
        budget_header = QLabel("💰 Budget Breakdown")
        budget_header.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 15px;
                color: #1E293B;
                background: transparent;
                border: none;
            }
        """)
        bc_layout.addWidget(budget_header)
        
        current_chart = None
        if BudgetPieChart:
            current_chart = BudgetPieChart()
            bc_layout.addWidget(current_chart)
        else:
            fallback_lbl = QLabel("📊 Chart Loading...")
            fallback_lbl.setAlignment(Qt.AlignCenter)
            fallback_lbl.setStyleSheet("""
                QLabel {
                    color: #94A3B8;
                    font-style: italic;
                    background: transparent;
                    border: none;
                }
            """)
            bc_layout.addWidget(fallback_lbl)
        
        bw = BudgetWorker(self.api, plan_data)
        currency = plan_data.get("currency", "USD")
        bw.finished_signal.connect(lambda res, c=current_chart, cur=currency: self.update_budget_chart(res, c, cur))
        self.start_worker(bw)

        row2.addWidget(budget_card, 1)
        self.feed_layout.insertLayout(self.feed_layout.count()-1, row2)

        # ==================== ITINERARY SECTION ====================
        itinerary = plan_data.get("itinerary", [])
        if itinerary:
            itinerary_header = QLabel("📋 Itinerary")
            itinerary_header.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: white;
                    margin-top: 15px;
                    background: transparent;
                    border: none;
                }
            """)
            self.feed_layout.insertWidget(self.feed_layout.count()-1, itinerary_header)
        
        for day in itinerary:
            day_card = GlassCard()
            day_layout = QVBoxLayout(day_card)
            day_layout.setContentsMargins(20, 18, 20, 18)
            day_layout.setSpacing(8)
            
            day_num = day.get('day', '?')
            day_title = day.get('activity') or day.get('title') or "Activity"
            
            title_lbl = QLabel(f"📅 Day {day_num}: {day_title}")
            title_lbl.setWordWrap(True) 
            title_lbl.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    font-size: 16px;
                    color: #3B82F6;
                    background: transparent;
                    border: none;
                }
            """)
            day_layout.addWidget(title_lbl)
            
            if "activities" in day and isinstance(day["activities"], list):
                for act in day["activities"]:
                    act_lbl = QLabel(f"• {act}")
                    act_lbl.setWordWrap(True) 
                    act_lbl.setStyleSheet("""
                        QLabel {
                            font-size: 14px;
                            color: #475569;
                            margin-left: 10px;
                            background: transparent;
                            border: none;
                        }
                    """)
                    day_layout.addWidget(act_lbl)
            
            self.feed_layout.insertWidget(self.feed_layout.count()-1, day_card)

        # Save state if needed
        if save and not self.is_loading_mode:
            self.chat_history_state.append({
                "type": "plan", 
                "content": {"title": title, "plan": plan_data}
            })
            self.save_state_to_server()

    # ============================================================================
    #                           BUDGET CHART
    # ============================================================================

    def update_budget_chart(self, breakdown_data, chart_widget, currency="USD"):
        """Parse and update budget chart data"""
        if not chart_widget or not breakdown_data:
            return

        clean_data = {}
        for category, text in breakdown_data.items():
            match = re.search(r'(\d+)', str(text).replace(",", ""))
            if match:
                clean_data[category] = int(match.group(1))
        
        chart_widget.update_data(clean_data, currency)

    # ============================================================================
    #                           IMAGE GENERATION
    # ============================================================================

    def trigger_image_generation(self, destination, interest, ver_id):
        """Start image generation worker"""
        print(f"🎨 Starting image generation for ver_id={ver_id}, dest={destination}")
        worker = ImageWorker(self.api, destination, interest)
        worker.finished_signal.connect(lambda b64: self._on_image_received(b64, ver_id))
        self.start_worker(worker)
    
    def _on_image_received(self, b64, ver_id):
        """Handle received image"""
        print(f"📷 Image received for ver_id={ver_id}, has_data={b64 is not None and len(b64) > 0 if b64 else False}")
        if b64:
            print(f"   Image data length: {len(b64)} chars")
        self.render_image_in_placeholder(b64, ver_id)

    def render_image_in_placeholder(self, b64, ver_id, save=True):
        """Render generated image in placeholder"""
        print(f"🖼️ render_image_in_placeholder called: ver_id={ver_id}, has_b64={b64 is not None}")
        layout = self.image_placeholders.get(ver_id)
        print(f"   Available placeholders: {list(self.image_placeholders.keys())}")
        if not layout:
            print(f"   ⚠️ No layout found for ver_id={ver_id}!")
            return
            
        # Clear loading placeholder
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        pix = QPixmap()
        loaded = False
        
        if b64:
            try:
                data = base64.b64decode(b64)
                pix.loadFromData(QByteArray(data))
                loaded = not pix.isNull()
            except:
                pass

        if not loaded:
            # Try fallback images
            base_dir = os.getcwd() 
            candidates = [
                os.path.join(base_dir, "assets", "globe_logo.png"),
                os.path.join(base_dir, "client", "assets", "globe_logo.png"),
            ]
            
            for path in candidates:
                if os.path.exists(path):
                    if pix.load(path):
                        loaded = True
                        break
            
            if not loaded:
                no_img_lbl = QLabel("🖼️")
                no_img_lbl.setStyleSheet("""
                    QLabel {
                        color: #94A3B8;
                        font-size: 48px;
                        background: transparent;
                        border: none;
                    }
                """)
                no_img_lbl.setAlignment(Qt.AlignCenter)
                layout.addWidget(no_img_lbl)
                return

        # Display image
        lbl = ClickableImage()
        lbl.setPixmap(pix.scaled(160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("border: none; background: transparent;")
        lbl.clicked.connect(lambda: ImagePopup(pix).exec())
        layout.addWidget(lbl)
        
        # Store image for PDF export
        if b64:
            self.current_image_b64 = b64
            print(f"📷 Image stored for PDF export ({len(b64)} chars)")

        if save and not self.is_loading_mode:
            content = b64 if b64 else "" 
            self.chat_history_state.append({"type": "image", "content": content})
            self.save_state_to_server()

    # ============================================================================
    #                           WEATHER
    # ============================================================================

    def fetch_weather(self, dest):
        """Fetch weather for destination"""
        if ver_id := self.current_active_ver_id:
            lbl = self.weather_labels.get(ver_id)
            if lbl:
                lbl.setText("⏳")
        
        w = WeatherWorker(self.api, dest)
        w.finished_signal.connect(self.update_weather_ui)
        self.start_worker(w)

    def update_weather_ui(self, data):
        """Update weather display"""
        if not self.current_active_ver_id:
            return
        
        # Store weather for PDF
        if data:
            self.current_weather = data
            print(f"🌤️ Weather stored for PDF: {data.get('temp', '--')}°C")
            
        lbl = self.weather_labels.get(self.current_active_ver_id)
        if lbl and data:
            icon = data.get('icon', '🌤️')
            temp = data.get('temp', '--')
            desc = data.get('desc', '')
            lbl.setText(f"{icon}\n{temp}°C")
            lbl.setToolTip(desc)
        elif lbl:
            lbl.setText("❌")

    # ============================================================================
    #                           CHAT FUNCTIONALITY
    # ============================================================================

    def on_send(self):
        """Handle send button click"""
        msg = self.chat_input.text().strip()
        self.chat_input.setText("")
        
        if not msg:
            return
        
        # 🛡️ SECURITY CHECK - Prompt Injection Protection
        if not validate_and_protect(chat_message=msg):
            return
            
        self.add_bubble(msg, True)
        
        selected_mode = self.mode_combo.currentText()
        selected_model = self.model_combo.currentText().lower()

        if "Question" in selected_mode:
            w = ChatWorker(self.api, msg, self.current_context, selected_model)
            w.finished_signal.connect(lambda ans: self.add_bubble(ans, False))
            self.start_worker(w)
        else:
            self.add_bubble("🔄 Refining your plan...", False)
            w = RefineWorker(self.api, self.trip_id, self.current_plan_data, msg, selected_model)
            w.finished.connect(lambda res: self.on_refine_done(res, msg))
            self.start_worker(w)

    def on_refine_done(self, res, msg):
        """Handle refine completion"""
        if res and "trip_plan" in res:
            self.current_plan_data = res["trip_plan"]
            self.current_context = json.dumps(res["trip_plan"], default=str, indent=2)
            self.render_trip_block(f"🛠️ {msg[:30]}...", res["trip_plan"], is_new=True)
        else:
            self.add_bubble("❌ Failed to refine plan. Please try again.", False)

    def add_bubble(self, text, is_user, save=True):
        """Add a chat bubble to the feed"""
        # Container for alignment
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        bubble = ChatBubble(text, is_user)
        bubble.setMaximumWidth(600)
        
        if is_user:
            container_layout.addStretch()
            container_layout.addWidget(bubble)
        else:
            container_layout.addWidget(bubble)
            container_layout.addStretch()
        
        self.feed_layout.insertWidget(self.feed_layout.count()-1, container)
        
        # Auto scroll
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))
        
        if save and not self.is_loading_mode:
            self.chat_history_state.append({
                "type": "text", 
                "content": text, 
                "is_user": is_user
            })
            self.save_state_to_server()

    # ============================================================================
    #                           STATE MANAGEMENT
    # ============================================================================

    def save_state_to_server(self):
        """Save chat history to server"""
        if not self.is_loading_mode:
            self.state_updated_signal.emit(self.chat_history_state)

    def scroll_to_item(self, item):
        """Scroll to selected trip version"""
        w = self.trip_widgets_map.get(id(item))
        if w:
            self.scroll_area.ensureWidgetVisible(w)

    # ============================================================================
    #                           PDF EXPORT
    # ============================================================================

    def save_pdf(self):
        """Export trip to PDF"""
        if not generate_trip_pdf:
            QMessageBox.warning(self, "Error", "PDF module not available")
            return
        
        # Debug: Check if image exists
        print(f"📷 Image available for PDF: {self.current_image_b64 is not None}")
        print(f"🌤️ Weather available: {self.current_weather is not None}")
        
        # Generate smart filename
        dest = self.current_plan_data.get("destination", "Trip")
        start = self.current_plan_data.get("start_date", "")
        default_name = f"Trip_to_{dest.replace(' ', '_')}"
        if start:
            default_name += f"_{start}"
        default_name += ".pdf"
            
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Trip PDF", 
            default_name, 
            "PDF Files (*.pdf)"
        )
        
        if filename:
            try:
                # Prepare weather info string
                weather_str = None
                if self.current_weather:
                    icon = self.current_weather.get('icon', '')
                    temp = self.current_weather.get('temp', '')
                    desc = self.current_weather.get('desc', '')
                    weather_str = f"{icon} {temp}°C - {desc}"
                
                generate_trip_pdf(
                    self.current_plan_data, 
                    filename,
                    image_base64=self.current_image_b64,
                    weather_info=weather_str
                )
                QMessageBox.information(self, "Success", "✅ PDF saved successfully!")
                if os.name == 'nt':
                    os.startfile(filename)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save PDF:\n{str(e)}")