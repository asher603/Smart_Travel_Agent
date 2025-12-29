import requests
from PySide6.QtCore import QObject, QThread, Signal

# --- Worker Class: האחראי על הרצת בקשות ברקע ---
class RequestWorker(QThread):
    success_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, target_func, *args, **kwargs):
        super().__init__()
        self.target_func = target_func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            # הרצת הפונקציה המקורית
            result = self.target_func(*self.args, **self.kwargs)
            
            # בדיקה אם חזרה שגיאה מהשרת
            if isinstance(result, dict) and "error" in result:
                self.error_signal.emit(str(result["error"]))
            else:
                self.success_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))

class APIService(QObject):
    def __init__(self, base_url="http://127.0.0.1:8000"):
        super().__init__()
        self.base_url = base_url
        self._active_workers = []

    def _cleanup_worker(self, worker):
        if worker in self._active_workers:
            self._active_workers.remove(worker)
        worker.deleteLater()

    # --- פונקציה בסיסית (סינכרונית) ---
    def post(self, endpoint, data, timeout=60):
        """ שליחת בקשת POST (סינכרונית) """
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.post(url, json=data, timeout=timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                try:
                    # ניסיון לשלוף את הודעת השגיאה מה-detail של FastAPI
                    detail = response.json().get("detail", response.text)
                    return {"error": detail}
                except:
                    return {"error": f"Server Error {response.status_code}"}
        except requests.exceptions.Timeout:
            return {"error": "Server took too long to respond."}
        except requests.exceptions.ConnectionError:
            return {"error": "Could not connect to server. Is it running?"}
        except Exception as e:
            return {"error": f"Request Error: {str(e)}"}

    def _run_async(self, func, args, on_success, on_error):
        """ מפעיל בקשה ב-Thread נפרד """
        worker = RequestWorker(func, *args)
        if on_success: worker.success_signal.connect(on_success)
        if on_error: worker.error_signal.connect(on_error)
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._active_workers.append(worker)
        worker.start()

    # --- פונקציות ה-API המותאמות לשרת החדש ---

    def login(self, username, password, on_success=None, on_error=None):
        payload = {"username": username, "password": password}
        if on_success:
            self._run_async(self.post, ("/login", payload), on_success, on_error)
        else:
            return self.post("/login", payload)

    def register(self, username, password, on_success=None, on_error=None):
        payload = {"username": username, "password": password}
        if on_success:
            self._run_async(self.post, ("/register", payload), on_success, on_error)
        else:
            return self.post("/register", payload)

    def generate_trip(self, trip_data, on_success=None, on_error=None):
        """ יצירת טיול חדש ושמירתו ב-DB """
        if on_success:
            # Timeout ארוך ליצירת טיול (10 דקות)
            self._run_async(self.post, ("/generate_trip", trip_data, 600), on_success, on_error)
        else:
            return self.post("/generate_trip", trip_data, timeout=600)

    def get_history_summary(self, username, on_success=None, on_error=None):
        """ שליפת רשימת הטיולים המקוצרת להיסטוריה """
        payload = {"username": username}
        if on_success:
            self._run_async(self.post, ("/get_history_summary", payload), on_success, on_error)
        else:
            return self.post("/get_history_summary", payload)

    def get_full_trip(self, trip_id, on_success=None, on_error=None):
        """ שליפת טיול מלא כולל צ'אט לפי ID """
        payload = {"trip_id": trip_id}
        if on_success:
            self._run_async(self.post, ("/get_full_trip", payload), on_success, on_error)
        else:
            return self.post("/get_full_trip", payload)

    def update_trip_state(self, trip_id, chat_history, on_success=None, on_error=None):
        """ עדכון היסטוריית הצ'אט (בועות) בשרת """
        payload = {"trip_id": trip_id, "chat_history": chat_history}
        if on_success:
            self._run_async(self.post, ("/update_trip_state", payload), on_success, on_error)
        else:
            return self.post("/update_trip_state", payload)

    def ask_question(self, question, context, on_success=None, on_error=None):
        """ שאלה לצ'אטבוט """
        payload = {"question": question, "context": context}
        if on_success:
            self._run_async(self.post, ("/ask_question", payload), on_success, on_error)
        else:
            return self.post("/ask_question", payload)