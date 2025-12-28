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
            # הרצת הפונקציה המקורית (למשל self.post)
            result = self.target_func(*self.args, **self.kwargs)
            
            # בדיקה אם חזרה שגיאה מהשרת
            if isinstance(result, dict) and "error" in result:
                self.error_signal.emit(result["error"])
            else:
                self.success_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))

class APIService(QObject):
    def __init__(self, base_url="http://127.0.0.1:8000"):
        super().__init__()
        self.base_url = base_url
        # רשימה לשמירת ה-Workers כדי שלא יימחקו מהזיכרון באמצע
        self._active_workers = []

    def _cleanup_worker(self, worker):
        if worker in self._active_workers:
            self._active_workers.remove(worker)
        worker.deleteLater()

    # --- פונקציה בסיסית (סינכרונית) ---
    def post(self, endpoint, data, timeout=60):
        """ שליחת בקשה רגילה (סינכרונית) - משמשת את ה-Workers """
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.post(url, json=data, timeout=timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                try:
                    return {"error": response.json().get("detail", response.text)}
                except:
                    return {"error": f"Server Error {response.status_code}"}
        except requests.exceptions.Timeout:
            return {"error": "Server took too long to respond."}
        except requests.exceptions.ConnectionError:
            return {"error": "Could not connect to server. Is it running?"}
        except Exception as e:
            return {"error": f"Connection Error: {str(e)}"}

    # --- פונקציות מעטפת חכמות (תומכות גם בסינכרוני וגם בא-סינכרוני) ---

    def _run_async(self, func, args, on_success, on_error):
        """ פונקציית עזר שמריצה את הבקשה ב-Thread נפרד """
        worker = RequestWorker(func, *args)
        
        if on_success:
            worker.success_signal.connect(on_success)
        if on_error:
            worker.error_signal.connect(on_error)
            
        # ניקוי עצמי בסיום
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        
        self._active_workers.append(worker)
        worker.start()

    def login(self, username, password, on_success=None, on_error=None):
        """ התחברות - תומכת ב-Callbacks למניעת קפיאת המסך """
        if on_success and on_error:
            self._run_async(self.post, ("/login", {"username": username, "password": password}), on_success, on_error)
        else:
            return self.post("/login", {"username": username, "password": password})

    def register(self, username, password, on_success=None, on_error=None):
        """ הרשמה """
        if on_success and on_error:
            self._run_async(self.post, ("/register", {"username": username, "password": password}), on_success, on_error)
        else:
            return self.post("/register", {"username": username, "password": password})

    def generate_trip(self, trip_data, on_success=None, on_error=None):
        """ יצירת טיול (פעולה כבדה) """
        # המרה לפורמט שהשרת מצפה לו
        payload = {
            "username": trip_data.get("username", "Guest"), # ברירת מחדל אם חסר
            "destination": trip_data["destination"],
            "origin": trip_data["origin"],
            "stops": "",
            "budget": trip_data["budget"],
            "currency": trip_data["currency"],
            "interest": trip_data["interest"],
            "duration": trip_data["duration"]
        }
        
        if on_success and on_error:
            # Timeout ארוך לטיול (10 דקות)
            self._run_async(self.post, ("/generate_trip", payload, 600), on_success, on_error)
        else:
            return self.post("/generate_trip", payload, timeout=600)

    def get_history(self, username, on_success=None, on_error=None):
        """ קבלת היסטוריה """
        def _get_history_sync():
            try:
                res = requests.get(f"{self.base_url}/history/{username}", timeout=10)
                if res.status_code == 200: return res.json()
                return []
            except: return []

        if on_success:
            worker = RequestWorker(_get_history_sync)
            worker.success_signal.connect(on_success)
            worker.finished.connect(lambda: self._cleanup_worker(worker))
            self._active_workers.append(worker)
            worker.start()
        else:
            return _get_history_sync()