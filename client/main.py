import sys
import re
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout,
                               QWidget, QLabel, QLineEdit, QStackedWidget,
                               QFrame, QSpinBox, QListWidget, QComboBox, QScrollArea, QSizePolicy)
from PySide6.QtCore import QThread, Signal, Qt, QSize
from PySide6.QtGui import QFont, QIcon, QColor
from api_service import APIService

# --- Styles ---
STYLESHEET = """
    QMainWindow { background-color: #f0f2f5; }
    
    /* Typography */
    QLabel { color: #333; font-family: 'Segoe UI', Arial; font-size: 14px; }
    QLabel#Header { font-size: 24px; font-weight: bold; color: #1a1a1a; }
    QLabel#SubHeader { font-size: 18px; font-weight: 600; color: #444; }
    QLabel#CardTitle { font-size: 16px; font-weight: bold; color: #007bff; }
    
    /* Inputs */
    QLineEdit, QSpinBox, QComboBox { 
        padding: 12px; 
        border: 1px solid #e0e0e0; 
        border-radius: 8px; 
        background-color: #ffffff; 
        font-size: 14px;
        color: #000;
    }
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border: 1px solid #007bff; }
    
    /* Buttons */
    QPushButton {
        background-color: #007bff; 
        color: white; 
        padding: 12px 20px; 
        border-radius: 8px; 
        font-weight: bold; 
        font-size: 14px;
        border: none;
    }
    QPushButton:hover { background-color: #0056b3; }
    
    QPushButton#SecondaryBtn {
        background-color: white; 
        color: #007bff; 
        border: 1px solid #007bff;
    }
    QPushButton#SecondaryBtn:hover { background-color: #f0f8ff; }

    /* Cards */
    QFrame#Card {
        background-color: white;
        border-radius: 12px;
        border: 1px solid #e6e6e6;
    }
    
    /* Scroll Area */
    QScrollArea { border: none; background-color: transparent; }
    QWidget#ScrollContents { background-color: transparent; }
"""

# --- Custom Widgets ---
class Card(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("Card")
        # Add a subtle shadow effect
        self.setGraphicsEffect(None) # Can add QGraphicsDropShadowEffect here if desired

# --- Worker Threads ---
class TripWorker(QThread):
    finished_signal = Signal(dict)
    def __init__(self, api, username, destination, budget, interest, days):
        super().__init__()
        self.api = api
        self.username = username
        self.dest = destination
        self.budget = budget
        self.interest = interest
        self.days = days

    def run(self):
        data = self.api.generate_trip(self.username, self.dest, self.budget, self.interest, self.days)
        self.finished_signal.emit(data)

class HistoryWorker(QThread):
    finished_signal = Signal(list)
    def __init__(self, api, username):
        super().__init__()
        self.api = api
        self.username = username

    def run(self):
        data = self.api.get_history(self.username)
        self.finished_signal.emit(data)

# --- Screens ---

class LoginScreen(QWidget):
    def __init__(self, switch_callback, api):
        super().__init__()
        self.switch_callback = switch_callback
        self.api = api
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        card = Card()
        card.setFixedWidth(400)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)

        title = QLabel("Smart Travel Login")
        title.setObjectName("Header")
        title.setAlignment(Qt.AlignCenter)
        
        instr = QLabel("Enter any username to start.")
        instr.setStyleSheet("color: #666;")
        instr.setAlignment(Qt.AlignCenter)
        
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username")
        
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.Password)
        
        login_btn = QPushButton("Login / Auto-Register")
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.clicked.connect(self.handle_login)

        card_layout.addWidget(title)
        card_layout.addWidget(instr)
        card_layout.addWidget(self.user_input)
        card_layout.addWidget(self.pass_input)
        card_layout.addWidget(login_btn)
        
        layout.addWidget(card)
        self.setLayout(layout)

    def handle_login(self):
        username = self.user_input.text()
        pwd = self.pass_input.text()
        if not username or not pwd:
            QMessageBox.warning(self, "Error", "Fill all fields")
            return
        
        res = self.api.login(username, pwd)
        if "error" not in res:
            self.switch_callback("dashboard", username)
        else:
            QMessageBox.critical(self, "Error", str(res["error"]))

class DashboardScreen(QWidget):
    def __init__(self, switch_callback, api):
        super().__init__()
        self.switch_callback = switch_callback
        self.api = api
        self.current_user = None

        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # Header Bar
        self.header_layout = QHBoxLayout()
        self.welcome_lbl = QLabel("Welcome!")
        self.welcome_lbl.setObjectName("SubHeader")
        
        self.hist_btn = QPushButton("My History")
        self.hist_btn.setObjectName("SecondaryBtn")
        self.hist_btn.clicked.connect(lambda: self.switch_callback("history", self.current_user))
        
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setStyleSheet("background-color: #dc3545; border: none;")
        self.logout_btn.clicked.connect(lambda: self.switch_callback("login", None))
        
        self.header_layout.addWidget(self.welcome_lbl)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.hist_btn)
        self.header_layout.addWidget(self.logout_btn)
        self.main_layout.addLayout(self.header_layout)

        # Content Stack (Switch between Input Form and Results)
        self.content_stack = QStackedWidget()
        self.main_layout.addWidget(self.content_stack)

        # 1. Input View
        self.input_view = QWidget()
        self.setup_input_view()
        self.content_stack.addWidget(self.input_view)

        # 2. Result View
        self.result_view = QWidget()
        self.setup_result_view()
        self.content_stack.addWidget(self.result_view)

    def setup_input_view(self):
        layout = QVBoxLayout(self.input_view)
        layout.setAlignment(Qt.AlignCenter)
        
        card = Card()
        card.setFixedWidth(500)
        form = QVBoxLayout(card)
        form.setSpacing(15)
        form.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Plan Your Next Adventure 🌍")
        title.setObjectName("Header")
        title.setAlignment(Qt.AlignCenter)
        
        self.dest_in = QLineEdit()
        self.dest_in.setPlaceholderText("Where to? (e.g. Tokyo)")
        
        row1 = QHBoxLayout()
        self.days_in = QSpinBox()
        self.days_in.setRange(1, 30)
        self.days_in.setSuffix(" Days")
        self.days_in.setValue(3)
        
        self.budget_in = QSpinBox()
        self.budget_in.setRange(100, 100000)
        self.budget_in.setPrefix("$")
        self.budget_in.setValue(1500)
        
        row1.addWidget(QLabel("Duration:"))
        row1.addWidget(self.days_in)
        row1.addSpacing(20)
        row1.addWidget(QLabel("Budget:"))
        row1.addWidget(self.budget_in)

        self.interest_in = QComboBox()
        self.interest_in.addItems(["General", "History", "Food", "Nature", "Shopping"])
        
        self.gen_btn = QPushButton("Generate Itinerary 🚀")
        self.gen_btn.setCursor(Qt.PointingHandCursor)
        self.gen_btn.clicked.connect(self.generate)

        form.addWidget(title)
        form.addSpacing(10)
        form.addWidget(QLabel("Destination"))
        form.addWidget(self.dest_in)
        form.addLayout(row1)
        form.addWidget(QLabel("Primary Interest"))
        form.addWidget(self.interest_in)
        form.addSpacing(10)
        form.addWidget(self.gen_btn)
        
        layout.addWidget(card)

    def setup_result_view(self):
        layout = QVBoxLayout(self.result_view)
        
        # New Search Button
        top_bar = QHBoxLayout()
        back_btn = QPushButton("← New Search")
        back_btn.setObjectName("SecondaryBtn")
        back_btn.setFixedWidth(150)
        back_btn.clicked.connect(self.reset_search)
        top_bar.addWidget(back_btn)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # Scroll Area for Cards
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("ScrollContents")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(20)
        self.scroll.setWidget(self.scroll_content)
        
        layout.addWidget(self.scroll)

    def set_user(self, username):
        self.current_user = username
        self.welcome_lbl.setText(f"Hello, {username}!")

    def generate(self):
        dest = self.dest_in.text()
        if not dest:
            QMessageBox.warning(self, "Oops", "Please enter a destination!")
            return
        
        self.gen_btn.setText("Generating... ⏳")
        self.gen_btn.setEnabled(False)
        
        self.worker = TripWorker(self.api, self.current_user, dest, 
                                 self.budget_in.value(), 
                                 self.interest_in.currentText(),
                                 self.days_in.value())
        self.worker.finished_signal.connect(self.on_trip_generated)
        self.worker.start()

    def on_trip_generated(self, data):
        self.gen_btn.setText("Generate Itinerary 🚀")
        self.gen_btn.setEnabled(True)
        
        if "error" in data:
            QMessageBox.critical(self, "Error", data["error"])
            return

        # Clear previous results
        for i in reversed(range(self.scroll_layout.count())): 
            self.scroll_layout.itemAt(i).widget().setParent(None)

        # --- Build Result Cards ---

        # 1. Recap Card
        recap_card = Card()
        recap_layout = QHBoxLayout(recap_card)
        recap_text = f"<b>Trip to {data['destination']}</b> ({data['days']} Days) | Budget: ${data['budget']}"
        lbl = QLabel(recap_text)
        lbl.setTextFormat(Qt.RichText)
        recap_layout.addWidget(lbl)
        self.scroll_layout.addWidget(recap_card)

        # 2. Weather Card
        weather_card = Card()
        w_layout = QHBoxLayout(weather_card)
        w_icon = QLabel("☀️") # Placeholder icon
        w_icon.setFont(QFont("Segoe UI Emoji", 30))
        w_info = QLabel(f"<b>Forecast:</b> {data.get('weather', 'N/A')}\nPack accordingly!")
        w_info.setTextFormat(Qt.RichText)
        w_layout.addWidget(w_icon)
        w_layout.addWidget(w_info)
        w_layout.addStretch()
        self.scroll_layout.addWidget(weather_card)

        # 3. Parse and Create Day Cards
        full_text = data.get('itinerary', '')
        
        # Regex to split by "**Day X:**" or "Day X:"
        # This regex looks for "Day <number>:"
        day_chunks = re.split(r'(?:\*\*Day|Day)\s+(\d+)[:\*\*]+', full_text)
        
        if len(day_chunks) > 1:
            # chunk[0] is usually intro text
            if day_chunks[0].strip():
                intro_card = Card()
                il = QVBoxLayout(intro_card)
                il_lbl = QLabel(day_chunks[0])
                il_lbl.setWordWrap(True)
                il_lbl.setTextFormat(Qt.MarkdownText)
                il.addWidget(il_lbl)
                self.scroll_layout.addWidget(intro_card)

            # Loop through matched days
            # re.split returns [intro, day_num, content, day_num, content...]
            for i in range(1, len(day_chunks), 2):
                day_num = day_chunks[i]
                content = day_chunks[i+1].strip()
                
                day_card = Card()
                dl = QVBoxLayout(day_card)
                
                title = QLabel(f"Day {day_num}")
                title.setObjectName("CardTitle")
                
                body = QLabel(content)
                body.setWordWrap(True)
                body.setTextFormat(Qt.MarkdownText) # Renders bold/lists nicely
                
                dl.addWidget(title)
                dl.addWidget(body)
                self.scroll_layout.addWidget(day_card)
        else:
            # Fallback if parsing fails
            fallback_card = Card()
            fl = QVBoxLayout(fallback_card)
            fl_lbl = QLabel(full_text)
            fl_lbl.setWordWrap(True)
            fl_lbl.setTextFormat(Qt.MarkdownText)
            fl.addWidget(fl_lbl)
            self.scroll_layout.addWidget(fallback_card)

        # Switch View
        self.content_stack.setCurrentIndex(1)

    def reset_search(self):
        self.content_stack.setCurrentIndex(0)

class HistoryScreen(QWidget):
    def __init__(self, switch_callback, api):
        super().__init__()
        self.switch_callback = switch_callback
        self.api = api
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QLabel("Your Trip History")
        header.setObjectName("Header")
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("border: none; background: transparent;")
        
        back_btn = QPushButton("Back to Dashboard")
        back_btn.setObjectName("SecondaryBtn")
        back_btn.clicked.connect(lambda: self.switch_callback("dashboard", self.current_user))
        
        layout.addWidget(header)
        layout.addWidget(self.list_widget)
        layout.addWidget(back_btn)
        
    def load_history(self, username):
        self.current_user = username
        self.list_widget.clear()
        
        self.worker = HistoryWorker(self.api, username)
        self.worker.finished_signal.connect(self.show_list)
        self.worker.start()
        
    def show_list(self, data):
        self.list_widget.clear()
        if not data:
            self.list_widget.addItem("No history found.")
            return
            
        for item in data:
            payload = item.get('payload', {})
            # Create a custom widget for list item to look like a card
            item_widget = Card()
            l = QHBoxLayout(item_widget)
            
            dest = payload.get('destination', 'Unknown')
            days = payload.get('days', '?')
            budget = payload.get('budget', '?')
            date = item.get('timestamp', '')[:10]
            
            txt = QLabel(f"<b>{dest}</b> ({days} Days)<br>Budget: ${budget}<br><span style='color:#777'>{date}</span>")
            txt.setTextFormat(Qt.RichText)
            
            l.addWidget(txt)
            
            # Add to list
            list_item = QListWidget() # Dummy for size
            # Actually, QListWidget with custom widgets is complex in PySide6 without a dedicated class
            # Simpler approach: Just text for now, or use QScrollArea for history too.
            # Let's stick to simple text for stability, but formatted nicely
            
            display_str = f"{date} | {dest} ({days} days) - ${budget}"
            self.list_widget.addItem(display_str)

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Travel Agent")
        self.resize(900, 700)
        self.setStyleSheet(STYLESHEET)
        
        self.api = APIService()
        self.stack = QStackedWidget()
        
        self.login = LoginScreen(self.switch_view, self.api)
        self.dashboard = DashboardScreen(self.switch_view, self.api)
        self.history = HistoryScreen(self.switch_view, self.api)
        
        self.stack.addWidget(self.login)
        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.history)
        
        self.setCentralWidget(self.stack)

    def switch_view(self, name, data=None):
        if name == "login":
            self.stack.setCurrentIndex(0)
        elif name == "dashboard":
            self.dashboard.set_user(data)
            self.stack.setCurrentIndex(1)
        elif name == "history":
            self.history.load_history(data)
            self.stack.setCurrentIndex(2)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())