import sys
import os
from PySide6.QtWidgets import QApplication
from core.api import APIService
from core.event_bus import EventBus
from core.shell import Shell
from modules.auth import AuthView, AuthPresenter
from modules.dashboard import DashboardView, DashboardPresenter, DashboardModel
from modules.history import HistoryView, HistoryPresenter, HistoryModel
from modules.trip_form import TripFormView, TripFormPresenter, TripFormModel
from modules.trip_viewer import TripViewerView, TripViewerPresenter, TripViewerModel

# 1. Fix path to allow importing from root
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

def load_stylesheet(app, path):
    """
    Reads the .qss file and applies it to the global application.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            style = f.read()
            app.setStyleSheet(style)
    except FileNotFoundError:
        print(f"Warning: Stylesheet not found at {path}")

def main():
    app = QApplication(sys.argv)
    
    # 2. Load Styles correctly (Reading the file)
    style_path = os.path.join(current_dir, "assets", "styles.qss")
    load_stylesheet(app, style_path)
    
    # 3. Initialize Core Services
    # The EventBus is the "Glue" that lets modules talk to the Shell
    event_bus = EventBus()
    api_service = APIService()
    
    # 4. Initialize the Shell (The Main Window Container)
    shell = Shell(event_bus)
    
    # 5. Initialize Microfrontends (MVP Wiring)
    
    # --- Module: Auth ---
    auth_view = AuthView() 
    # The Presenter is created, but we don't need to store it in a variable 
    # if it attaches itself to the view/signals. However, keeping a reference is good practice.
    auth_presenter = AuthPresenter(auth_view, api_service, event_bus)
    # Register the view into the Shell's stack (Index 0)
    shell.register_module(0, auth_view)

    # --- Module: Dashboard ---
    dashboard_view = DashboardView()
    dashboard_presenter = DashboardPresenter(dashboard_view, DashboardModel(), event_bus)
    shell.register_module(1, dashboard_view)

    # --- Module: History ---
    history_view = HistoryView()
    history_presenter = HistoryPresenter(history_view, HistoryModel(), api_service, event_bus)
    shell.register_module(2, history_view)
    
    # --- Module: Trip Form ---
    trip_form_view = TripFormView()
    trip_form_presenter = TripFormPresenter(trip_form_view, TripFormModel(), api_service, event_bus)
    shell.register_module(3, trip_form_view)

    # --- Module: Trip Viewer ---
    trip_viewer_view = TripViewerView()
    trip_viewer_presenter = TripViewerPresenter(trip_viewer_view, TripViewerModel(), api_service, event_bus)
    shell.register_module(4, trip_viewer_view)

    # 6. Launch
    shell.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()