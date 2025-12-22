from PySide6.QtCore import QThread, Signal

class TripWorker(QThread):
    finished_signal = Signal(dict)
    
    # --- עדכון: קולט את כל הפרמטרים החדשים ---
    def __init__(self, api, u, dest, origin, stops, b, curr, i, days):
        super().__init__()
        self.api = api
        self.u = u
        self.dest = dest
        self.origin = origin
        self.stops = stops
        self.b = b
        self.curr = curr
        self.i = i
        self.days = days

    def run(self):
        # שליחה לשרת עם כל הנתונים
        data = self.api.generate_trip(
            self.u, self.dest, self.origin, self.stops, 
            self.b, self.curr, self.i, self.days
        )
        self.finished_signal.emit(data)

class HistoryWorker(QThread):
    finished_signal = Signal(list)
    def __init__(self, api, u):
        super().__init__()
        self.api, self.u = api, u
    def run(self):
        self.finished_signal.emit(self.api.get_history(self.u))