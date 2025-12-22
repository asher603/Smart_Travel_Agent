from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget
from client.logic.workers import HistoryWorker

class HistoryScreen(QWidget):
    def __init__(self, switch_cb, api):
        super().__init__()
        l = QVBoxLayout(self)
        l.setContentsMargins(30,30,30,30)
        l.addWidget(QLabel("History"))
        self.lst = QListWidget()
        l.addWidget(self.lst)
        btn = QPushButton("Back")
        btn.clicked.connect(lambda: switch_cb("dashboard", None))
        l.addWidget(btn)
        self.api = api
    
    def load_history(self, u):
        self.lst.clear()
        self.w = HistoryWorker(self.api, u)
        self.w.finished_signal.connect(self.add_items)
        self.w.start()
    
    def add_items(self, data):
        for i in data:
            pl = i.get('payload', {})
            self.lst.addItem(f"{pl.get('destination')} - {pl.get('days')} days")