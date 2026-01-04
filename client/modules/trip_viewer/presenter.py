from modules.trip_viewer.workers import (
    ImageWorker, ChatWorker, WeatherWorker, RefineWorker, StateSaverWorker
)
from utils.pdf_generator import generate_trip_pdf 

class TripViewerPresenter:
    def __init__(self, view, model, api_service, event_bus):
        self.view = view
        self.model = model
        self.api = api_service
        self.bus = event_bus

        # Connect Signals
        self.view.send_requested.connect(self.handle_chat)
        self.view.back_requested.connect(self.go_back)
        self.view.pdf_requested.connect(self.handle_pdf)
        # Note: Flight search logic can be added similarly

    def init_new_trip(self, trip_data, username):
        self.model.username = username
        self.model.trip_id = trip_data.get("trip_id")
        self.model.current_plan = trip_data
        self.model.current_context = f"Dest: {trip_data.get('destination')}"
        
        self.view.reset_view()
        self.view.btn_pdf.setVisible(True)
        self._render_version("Initial Plan", trip_data, save=True)

    def load_existing_trip(self, full_data):
        self.view.reset_view()
        self.model.trip_id = full_data.get("id")
        self.model.username = full_data.get("username")
        self.model.current_plan = {} # Will be set by history
        
        # Replay History
        for item in full_data.get("chat_history", []):
            t = item.get("type"); c = item.get("content")
            if t == "text": 
                self.view.add_bubble(c, item.get("is_user"))
            elif t == "plan": 
                self.model.current_plan = c["plan"]
                self.model.version_counter += 1
                ver_id = self.model.version_counter
                self.view.render_trip_block(ver_id, c["title"], c["plan"])
            elif t == "image":
                # Assuming previous render increased version_counter
                self.view.set_image(self.model.version_counter, c)

        self.view.btn_pdf.setVisible(True)
        # Fetch fresh weather for the loaded destination
        dest = self.model.current_plan.get("destination")
        if dest: self._fetch_weather(dest, self.model.version_counter)

    def handle_chat(self, msg, mode):
        self.view.add_bubble(msg, is_user=True)
        self._save_history("text", msg, is_user=True)

        if "Question" in mode:
            loading = self.view.add_bubble("Thinking...", is_user=False)
            worker = ChatWorker(self.api, msg, self.model.current_context)
            worker.finished_signal.connect(lambda ans: self._on_chat_reply(loading, ans))
            worker.start() # Note: Keep track of active workers in a real app
        else:
            loading = self.view.add_bubble("Refining plan...", is_user=False)
            worker = RefineWorker(self.api, self.model.current_plan, msg)
            worker.finished.connect(lambda res: self._on_refine_reply(loading, res, msg))
            worker.start()

    def _on_chat_reply(self, bubble, text):
        self.view.update_bubble(bubble, text)
        self._save_history("text", text, is_user=False)

    def _on_refine_reply(self, bubble, response, instruction):
        if response and "trip_plan" in response:
            bubble.deleteLater()
            new_plan = response["trip_plan"]
            self.model.current_plan = new_plan
            self._render_version(f"Fix: {instruction}", new_plan, save=True)
        else:
            self.view.update_bubble(bubble, "Failed to update plan.")

    def _render_version(self, title, plan, save=False):
        self.model.version_counter += 1
        ver_id = self.model.version_counter
        
        self.view.render_trip_block(ver_id, title, plan)
        
        if save:
            self._save_history("plan", {"title": title, "plan": plan})

        # Trigger Side Effects
        dest = plan.get("destination", "Trip")
        
        # Image
        img_worker = ImageWorker(self.api, dest, "travel")
        img_worker.finished_signal.connect(lambda b64: self._on_image_ready(ver_id, b64))
        img_worker.start()

        # Weather
        self._fetch_weather(dest, ver_id)

    def _fetch_weather(self, dest, ver_id):
        w_worker = WeatherWorker(self.api, dest)
        w_worker.finished_signal.connect(lambda d: self.view.update_weather(ver_id, f"{d.get('temp', '?')}°C {d.get('icon','')}"))
        w_worker.start()

    def _on_image_ready(self, ver_id, b64):
        self.view.set_image(ver_id, b64)
        self._save_history("image", b64)

    def _save_history(self, type_, content, is_user=None):
        entry = {"type": type_, "content": content}
        if is_user is not None: entry["is_user"] = is_user
        
        self.model.history_state.append(entry)
        
        # Auto-save to server
        if self.model.trip_id:
            worker = StateSaverWorker(self.api, self.model.trip_id, self.model.history_state)
            worker.start()

    def handle_pdf(self):
        # ... (PDF generation logic using self.model.current_plan) ...
        # Can import QFileDialog inside logic or trigger view to ask for path
        print("PDF Requested")

    def go_back(self):
        self.bus.publish("NAVIGATE", {"index": 1, "username": self.model.username})