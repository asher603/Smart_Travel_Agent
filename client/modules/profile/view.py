import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, 
    QGridLayout, QProgressBar, QTabWidget, QSlider, QLineEdit, 
    QMessageBox, QGraphicsDropShadowEffect, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import QColor, QFont, QPainter, QLinearGradient, QGradient

# --- ייבוא ספריית הגרפים (בתוך try/except למניעת קריסות אם חסר) ---
try:
    from PySide6.QtCharts import (
        QChart, QChartView, QBarSeries, QBarSet, 
        QBarCategoryAxis, QValueAxis
    )
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False
    print("⚠️ Warning: QtCharts not installed. Graph will not show.")

# ============================================================================
# רכיבים מעוצבים (Custom Widgets) - לשימוש חוזר
# ============================================================================

class GlassFrame(QFrame):
    """מסגרת בסיסית עם עיצוב זכוכית (שקוף למחצה)"""
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)

class StatCard(GlassFrame):
    """כרטיס סטטיסטיקה המציג אייקון, ערך וכותרת"""
    def __init__(self, icon, title, value_color="#e3f2fd"):
        super().__init__()
        
        # Layout ראשי לכרטיס
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        
        # האייקון למעלה
        self.lbl_icon = QLabel(icon)
        self.lbl_icon.setStyleSheet("font-size: 28px; background: transparent; border: none;")
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        
        # הערך המרכזי (המספר)
        self.lbl_value = QLabel("0")
        self.lbl_value.setStyleSheet(f"""
            font-size: 22px; 
            font-weight: bold; 
            color: {value_color}; 
            background: transparent; 
            border: none;
        """)
        self.lbl_value.setAlignment(Qt.AlignCenter)
        
        # הכותרת הקטנה למטה
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("""
            font-size: 12px; 
            color: #dddddd; 
            background: transparent; 
            border: none;
        """)
        self.lbl_title.setAlignment(Qt.AlignCenter)

        # הוספה ללאייאוט
        layout.addWidget(self.lbl_icon)
        layout.addWidget(self.lbl_value)
        layout.addWidget(self.lbl_title)

    def set_value(self, val):
        self.lbl_value.setText(str(val))


class TagButton(QPushButton):
    """כפתור 'תגית' (Chip) לבחירת תחומי עניין"""
    def __init__(self, text, icon=""):
        super().__init__(f"{icon} {text}")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(40)
        
        # עיצוב הכפתור במצבים שונים (רגיל, לחוץ, מעבר עכבר)
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 20px;
                color: #eeeeee;
                font-size: 14px;
                padding: 0 15px;
                font-weight: 500;
            }
            QPushButton:checked {
                background-color: rgba(33, 150, 243, 0.3);
                border: 1px solid #2196f3;
                color: #2196f3;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)


class StyledInput(QLineEdit):
    """שדה קלט טקסט מעוצב בסגנון זכוכית"""
    def __init__(self, placeholder, is_password=False):
        super().__init__()
        self.setPlaceholderText(placeholder)
        if is_password:
            self.setEchoMode(QLineEdit.Password)
        
        self.setFixedHeight(45)
        
        # עיצוב השדה
        self.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 10px;
                padding: 0 15px;
                font-size: 14px;
                color: white;
            }
            QLineEdit:focus {
                border: 2px solid #2196f3;
                background-color: rgba(255, 255, 255, 0.15);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.5);
            }
        """)

# ============================================================================
# Main Profile View Class
# ============================================================================

class ProfileView(QWidget):
    # הגדרת סיגנלים לתקשורת החוצה (ל-Presenter)
    back_signal = Signal()
    logout_signal = Signal()
    save_prefs_signal = Signal(dict)
    save_identity_signal = Signal(dict)
    change_pass_signal = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.tags = {}  # מילון לשמירת כפתורי התגיות
        self.chart_view = None # משתנה לשמירת הגרף
        self.chart = None
        
        self.setup_ui()

    def setup_ui(self):
        """בניית כל ממשק המשתמש"""
        
        # לאייאוט ראשי
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---------------------------------------------------------
        # 1. Header Area (החלק העליון הכחול)
        # ---------------------------------------------------------
        header = QFrame()
        header.setFixedHeight(180)
        # גרדיאנט כחול יוקרתי לרקע הכותרת
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1565c0, stop:1 #0d47a1);
                border-bottom-left-radius: 30px;
                border-bottom-right-radius: 30px;
            }
        """)
        
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(25, 20, 25, 20)

        # שורת כפתור חזרה
        top_bar = QHBoxLayout()
        self.btn_back = QPushButton("🔙 Back to Dashboard")
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.setStyleSheet("""
            QPushButton {
                color: white;
                background: transparent;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                text-decoration: underline;
                color: #e3f2fd;
            }
        """)
        self.btn_back.clicked.connect(self.back_signal.emit)
        top_bar.addWidget(self.btn_back)
        top_bar.addStretch() # דחיפת הכפתור שמאלה
        header_layout.addLayout(top_bar)

        # אזור פרטי המשתמש (תמונה + טקסט)
        user_info_layout = QHBoxLayout()
        user_info_layout.setSpacing(20)

        # תמונת פרופיל (Avatar)
        self.avatar = QLabel("👤")
        self.avatar.setFixedSize(80, 80)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 40px;
                font-size: 40px;
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.5);
            }
        """)

        # טקסט שם ומייל
        text_layout = QVBoxLayout()
        self.lbl_name = QLabel("Guest")
        self.lbl_name.setStyleSheet("""
            font-size: 26px; 
            font-weight: bold; 
            color: white; 
            background: transparent; 
            border: none;
        """)
        
        self.lbl_email = QLabel("")
        self.lbl_email.setStyleSheet("""
            font-size: 14px; 
            color: #bbdefb; 
            background: transparent; 
            border: none;
        """)
        
        text_layout.addWidget(self.lbl_name)
        text_layout.addWidget(self.lbl_email)
        text_layout.addStretch()

        user_info_layout.addWidget(self.avatar)
        user_info_layout.addLayout(text_layout)
        user_info_layout.addStretch()
        
        header_layout.addLayout(user_info_layout)
        main_layout.addWidget(header)

        # ---------------------------------------------------------
        # 2. Tabs Area (אזור הלשוניות)
        # ---------------------------------------------------------
        self.tabs = QTabWidget()
        # עיצוב הלשוניות עצמן (שקוף וmodern)
        self.tabs.setStyleSheet("""
            QTabWidget::pane { 
                border: none; 
                background: transparent; 
            }
            QTabWidget::tab-bar { 
                alignment: center; 
            }
            QTabBar::tab {
                background: transparent;
                color: #bbbbbb;
                font-size: 15px;
                font-weight: 600;
                padding: 12px 25px;
                margin-top: 10px;
                margin-bottom: 5px;
            }
            QTabBar::tab:selected {
                color: #42a5f5;
                border-bottom: 3px solid #42a5f5;
            }
            QTabBar::tab:hover {
                color: #42a5f5;
                background: rgba(255, 255, 255, 0.05);
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
        """)

        # יצירת שלושת המסכים (טאבים)
        self.tab_stats = self.create_stats_tab()
        self.tab_prefs = self.create_prefs_tab()
        self.tab_identity = self.create_identity_tab()

        self.tabs.addTab(self.tab_stats, "🏆 My Legend")
        self.tabs.addTab(self.tab_prefs, "🧠 AI DNA")
        self.tabs.addTab(self.tab_identity, "🆔 Identity")

        main_layout.addWidget(self.tabs)

    # ========================================================================
    # TAB 1: סטטיסטיקות וגרף
    # ========================================================================
    def create_stats_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        # -- אזור התקדמות דרגה --
        lbl_level_title = QLabel("Level Progress")
        lbl_level_title.setStyleSheet("color: #eeeeee; font-weight: bold; font-size: 16px;")
        layout.addWidget(lbl_level_title)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(14)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 7px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #42a5f5, stop:1 #1e88e5);
                border-radius: 7px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.lbl_next_level_hint = QLabel("Plan more trips to level up...")
        self.lbl_next_level_hint.setStyleSheet("color: #bbbbbb; font-size: 12px; font-style: italic;")
        layout.addWidget(self.lbl_next_level_hint)

        layout.addSpacing(15)

        # -- גריד הכרטיסים (Stats Cards) --
        grid = QGridLayout()
        grid.setSpacing(15)

        self.card_trips = StatCard("✈️", "Total Trips", "#4fc3f7")
        self.card_budget = StatCard("💰", "Total Budget", "#66bb6a")
        self.card_days = StatCard("📅", "Days Traveled", "#ffa726")
        self.card_last = StatCard("📍", "Last Destination", "#ab47bc")

        grid.addWidget(self.card_trips, 0, 0)
        grid.addWidget(self.card_budget, 0, 1)
        grid.addWidget(self.card_days, 1, 0)
        grid.addWidget(self.card_last, 1, 1)

        layout.addLayout(grid)
        layout.addSpacing(25)

        # -- אזור הגרף (Chart Area) --
        lbl_chart_title = QLabel("📊 Recent Trip Budgets")
        lbl_chart_title.setStyleSheet("color: #eeeeee; font-weight: bold; font-size: 16px;")
        layout.addWidget(lbl_chart_title)
        
        # מיכל לגרף
        chart_container = GlassFrame()
        chart_layout = QVBoxLayout(chart_container)
        
        if CHARTS_AVAILABLE:
            self.setup_chart() # פונקציית עזר להקמת הגרף
            chart_layout.addWidget(self.chart_view)
        else:
            lbl_error = QLabel("QtCharts library is missing. Install PySide6-Charts.")
            lbl_error.setStyleSheet("color: red;")
            chart_layout.addWidget(lbl_error)
            
        layout.addWidget(chart_container)
        layout.addStretch()

        return widget

    def setup_chart(self):
        """פונקציה פנימית לאתחול הגרף בפעם הראשונה"""
        self.chart = QChart()
        self.chart.setBackgroundVisible(False)  # רקע שקוף לגרף עצמו
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.legend().setVisible(False)   # הסתרת המקרא כי זה ברור

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setStyleSheet("background: transparent;")
        self.chart_view.setFixedHeight(250) # גובה קבוע

        # יצירת צירים (Axes) ריקים כרגע
        self.axis_x = QBarCategoryAxis()
        self.axis_x.setLabelsColor(QColor("white")) # טקסט לבן בציר X
        self.axis_x.setGridLineVisible(False)
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        
        self.axis_y = QValueAxis()
        self.axis_y.setLabelsColor(QColor("white")) # טקסט לבן בציר Y
        self.axis_y.setGridLineColor(QColor(255, 255, 255, 30)) # קווי רשת חלשים
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)

    # ========================================================================
    # TAB 2: העדפות AI (Sliders + Tags)
    # ========================================================================
    def create_prefs_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        layout.addWidget(QLabel("🧠 Customize Your AI Agent"))

        # מסגרת לסליידרים
        sliders_frame = GlassFrame()
        sf_layout = QVBoxLayout(sliders_frame)
        sf_layout.setContentsMargins(20, 20, 20, 20)
        sf_layout.setSpacing(15)

        # סליידר 1: קצב טיול
        lbl_pace = QLabel("🚀 Trip Pace (Chill vs. Intense)")
        lbl_pace.setStyleSheet("color: #eeeeee;")
        sf_layout.addWidget(lbl_pace)

        self.slider_pace = QSlider(Qt.Horizontal)
        self.slider_pace.setRange(0, 100)
        # עיצוב מותאם לסליידר
        self.slider_pace.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(255, 255, 255, 0.2);
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #2196f3;
                border-radius: 7px;
                width: 14px;
                height: 14px;
                margin: -3px 0;
            }
        """)
        sf_layout.addWidget(self.slider_pace)

        # סליידר 2: יוקרה
        lbl_lux = QLabel("💎 Luxury Level (Budget vs. Royal)")
        lbl_lux.setStyleSheet("color: #eeeeee;")
        sf_layout.addWidget(lbl_lux)

        self.slider_lux = QSlider(Qt.Horizontal)
        self.slider_lux.setRange(0, 100)
        self.slider_lux.setStyleSheet("""
            QSlider::groove:horizontal {
                background: rgba(255, 255, 255, 0.2);
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #ab47bc;
                border-radius: 7px;
                width: 14px;
                height: 14px;
                margin: -3px 0;
            }
        """)
        sf_layout.addWidget(self.slider_lux)
        layout.addWidget(sliders_frame)

        # אזור התגיות (Tags)
        layout.addSpacing(10)
        lbl_tags = QLabel("❤️ What do you love?")
        lbl_tags.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(lbl_tags)

        tags_layout = QGridLayout()
        tags_layout.setSpacing(10)
        
        # רשימת התגיות ליצירה
        tag_definitions = [
            ("Nature", "🌲", 0, 0), 
            ("Foodie", "🍕", 0, 1), 
            ("History", "🏛️", 0, 2), 
            ("Shopping", "🛍️", 1, 0),
            ("Nightlife", "🥂", 1, 1), 
            ("Art", "🎨", 1, 2)
        ]

        for name, icon, r, c in tag_definitions:
            btn = TagButton(name, icon)
            self.tags[name.lower()] = btn # שמירה במילון לגישה נוחה אח"כ
            tags_layout.addWidget(btn, r, c)

        layout.addLayout(tags_layout)
        layout.addStretch()

        # כפתור שמירה
        self.btn_save_prefs = QPushButton("💾 Save AI Preferences")
        self.btn_save_prefs.setCursor(Qt.PointingHandCursor)
        self.btn_save_prefs.setFixedHeight(45)
        self.btn_save_prefs.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #43a047, stop:1 #66bb6a);
                color: white; 
                font-weight: bold; 
                border-radius: 10px; 
                font-size: 16px; 
                border: none;
            }
            QPushButton:hover {
                background: #4caf50;
            }
        """)
        self.btn_save_prefs.clicked.connect(self.on_save_prefs_click)
        layout.addWidget(self.btn_save_prefs)

        return widget

    # ========================================================================
    # TAB 3: זהות ואבטחה (Identity)
    # ========================================================================
    def create_identity_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        # כותרת פרטים אישיים
        layout.addWidget(QLabel("📝 Personal Details"))
        
        self.inp_email = StyledInput("Email Address (for Calendar Invites)")
        layout.addWidget(self.inp_email)
        
        self.btn_update_id = QPushButton("Update Email")
        self.btn_update_id.setCursor(Qt.PointingHandCursor)
        self.btn_update_id.setStyleSheet("""
            QPushButton {
                background: #1976d2; 
                color: white; 
                padding: 10px; 
                border-radius: 8px; 
                font-weight: bold; 
                border: none;
            }
            QPushButton:hover { background: #1565c0; }
        """)
        self.btn_update_id.clicked.connect(self.on_save_identity_click)
        layout.addWidget(self.btn_update_id)

        # קו מפריד
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background: rgba(255,255,255,0.2);")
        layout.addWidget(line)

        # כותרת אבטחה
        layout.addWidget(QLabel("🔒 Security"))
        
        self.inp_old_pass = StyledInput("Old Password", is_password=True)
        layout.addWidget(self.inp_old_pass)
        
        self.inp_new_pass = StyledInput("New Password", is_password=True)
        layout.addWidget(self.inp_new_pass)
        
        self.btn_change_pass = QPushButton("Change Password")
        self.btn_change_pass.setCursor(Qt.PointingHandCursor)
        self.btn_change_pass.setStyleSheet("""
            QPushButton {
                background: #fb8c00; 
                color: white; 
                padding: 10px; 
                border-radius: 8px; 
                font-weight: bold; 
                border: none;
            }
            QPushButton:hover { background: #f57c00; }
        """)
        self.btn_change_pass.clicked.connect(self.on_change_pass_click)
        layout.addWidget(self.btn_change_pass)

        layout.addStretch()

        # כפתור התנתקות
        self.btn_logout = QPushButton("🚪 Log Out")
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        self.btn_logout.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 0, 0, 0.1); 
                color: #ef5350; 
                border: 1px solid #ef5350; 
                padding: 12px; 
                border-radius: 10px; 
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 0.2);
            }
        """)
        self.btn_logout.clicked.connect(self.logout_signal.emit)
        layout.addWidget(self.btn_logout)

        return widget

    # ========================================================================
    # פונקציות עזר פנימיות (לטיפול בלחיצות כפתור)
    # ========================================================================
    def on_save_prefs_click(self):
        # איסוף המידע מהסליידרים והכפתורים
        prefs = {
            "pace": self.slider_pace.value(),
            "luxury": self.slider_lux.value()
        }
        for key, btn in self.tags.items():
            prefs[key] = btn.isChecked()
        
        # שליחת סיגנל ל-Presenter
        self.save_prefs_signal.emit(prefs)
        
        # פידבק ויזואלי למשתמש
        self.btn_save_prefs.setText("Saved! ✅")
        self.btn_save_prefs.setEnabled(False)
        QTimer.singleShot(2000, lambda: self._reset_save_btn())

    def _reset_save_btn(self):
        self.btn_save_prefs.setText("💾 Save AI Preferences")
        self.btn_save_prefs.setEnabled(True)

    def on_save_identity_click(self):
        data = {
            "email": self.inp_email.text()
        }
        self.save_identity_signal.emit(data)

    def on_change_pass_click(self):
        self.change_pass_signal.emit(self.inp_old_pass.text(), self.inp_new_pass.text())

    # ========================================================================
    # UPDATE VIEW - הפונקציה הראשית שמעדכנת את כל המסך
    # ========================================================================
    def update_view(self, data):
        
        # 1. עדכון כותרת (שם ותמונה)
        # --- הוספנו את השורות האלו כדי שהשם יתעדכן ---
        username = data.get("username", "Guest")
        self.lbl_name.setText(username.capitalize())
        # ---------------------------------------------

        self.lbl_email.setText(data.get("email", ""))

        # 2. עדכון סטטיסטיקות
        self.progress_bar.setValue(data.get("level_progress", 0))
        self.lbl_next_level_hint.setText(data.get("next_level_hint", ""))
        
        self.card_trips.set_value(data.get("trip_count", 0))
        self.card_days.set_value(data.get("days_traveled", 0))
        self.card_last.set_value(data.get("last_trip_dest", "-"))

        # פורמט תקציב (מניעת קריסה אם הערך הוא טקסט)
        try:
            raw_budget = str(data.get("total_budget", 0)).replace("$", "").replace(",", "")
            clean_val = int(float(raw_budget))
            self.card_budget.set_value(f"${clean_val:,}")
        except:
            self.card_budget.set_value(str(data.get("total_budget", 0)))

        # 3. עדכון הגרף (Chart)
        if CHARTS_AVAILABLE and self.chart and "chart_data" in data:
            chart_data = data["chart_data"]
            labels = chart_data.get("labels", [])
            values = chart_data.get("values", [])
            
            # אם יש נתונים, נצייר את הגרף
            if labels and values:
                self.chart.removeAllSeries()
                
                series = QBarSeries()
                bar_set = QBarSet("Budget ($)")
                bar_set.setColor(QColor("#42a5f5"))
                bar_set.setBorderColor(QColor("#42a5f5"))
                
                for val in values:
                    bar_set.append(val)
                
                series.append(bar_set)
                self.chart.addSeries(series)
                
                self.axis_x.clear()
                self.axis_x.append(labels)
                series.attachAxis(self.axis_x)
                
                max_val = max(values) if values else 1000
                self.axis_y.setRange(0, max_val * 1.1)
                series.attachAxis(self.axis_y)

        # 4. עדכון העדפות (Preferences)
        prefs = data.get("preferences", {})
        self.slider_pace.setValue(prefs.get("pace", 50))
        self.slider_lux.setValue(prefs.get("luxury", 50))
        
        for key, btn in self.tags.items():
            if key in prefs:
                btn.setChecked(prefs[key])

        # 5. עדכון שדות זהות
        if not self.inp_email.hasFocus():
            self.inp_email.setText(data.get("email", ""))