import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QLineEdit
from api_service import APIService

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Travel Agent - MVP")
        self.resize(400, 300)
        
        self.api = APIService()

        # Layout Setup
        layout = QVBoxLayout()
        
        self.label = QLabel("Enter Destination:")
        layout.addWidget(self.label)
        
        self.input_field = QLineEdit()
        layout.addWidget(self.input_field)

        self.btn = QPushButton("Generate Trip")
        self.btn.clicked.connect(self.on_click)
        layout.addWidget(self.btn)

        self.result_label = QLabel("Result will appear here...")
        layout.addWidget(self.result_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def on_click(self):
        dest = self.input_field.text()
        self.result_label.setText("Loading...")
        # קריאה לשרת
        data = self.api.get_trip_plan(dest)
        self.result_label.setText(str(data))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())