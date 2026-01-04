from PySide6.QtWidgets import QMainWindow, QStackedWidget

class Shell(QMainWindow):
    def __init__(self, event_bus):
        super().__init__()
        self.setWindowTitle("Smart Travel Agent ✈️")
        self.setGeometry(100, 100, 1200, 800)
        
        self.event_bus = event_bus
        self.container = QStackedWidget()
        self.setCentralWidget(self.container)
        
        # Subscribe to navigation events
        self.event_bus.subscribe("NAVIGATE", self.on_navigate)

    def register_module(self, index, widget):
        self.container.insertWidget(index, widget)

    def on_navigate(self, data):
        target_index = data.get("index", 0)
        self.container.setCurrentIndex(target_index)