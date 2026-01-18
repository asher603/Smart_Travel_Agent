import sys
import os
from PySide6.QtWidgets import QApplication
# Core Services
from core.api import APIService
from core.event_bus import EventBus
from core.shell import Shell
# Module Imports
from modules.auth import AuthView, AuthPresenter
from modules.dashboard import DashboardView, DashboardPresenter, DashboardModel
from modules.history import HistoryView, HistoryPresenter, HistoryModel
from modules.trip_form import TripFormView, TripFormPresenter, TripFormModel
from modules.trip_viewer import TripViewerView, TripViewerPresenter, TripViewerModel
from modules.profile.view import ProfileView
from modules.profile.presenter import ProfilePresenter
from modules.profile.model import ProfileModel

# 1. Fix path to allow importing from root
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

def load_stylesheet(app, path):
    """Reads the .qss file and applies it to the global application."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            style = f.read()
            app.setStyleSheet(style)
    except FileNotFoundError:
        print(f"Warning: Stylesheet not found at {path}")

def main():
    app = QApplication(sys.argv)
    
    # 2. Load Styles
    style_path = os.path.join(current_dir, "assets", "styles.qss")
    load_stylesheet(app, style_path)
    
    # 3. Initialize Core Services
    event_bus = EventBus()
    api_service = APIService()
    
    # 4. Initialize the Shell
    shell = Shell(event_bus)
    
    # 5. Initialize Microfrontends
    # Note: We are registering them in the specific order corresponding to the index
    
    # Index 0: Auth
    auth_view = AuthView() 
    auth_presenter = AuthPresenter(auth_view, api_service, event_bus)
    shell.register_module(0, auth_view)

    # Index 1: Dashboard
    dashboard_view = DashboardView()
    dashboard_presenter = DashboardPresenter(dashboard_view, DashboardModel(), event_bus)
    shell.register_module(1, dashboard_view)

    # Index 2: History
    history_view = HistoryView()
    history_presenter = HistoryPresenter(history_view, HistoryModel(), api_service, event_bus)
    shell.register_module(2, history_view)
    
    # Index 3: Trip Form
    trip_form_view = TripFormView()
    trip_form_presenter = TripFormPresenter(trip_form_view, TripFormModel(), api_service, event_bus)
    shell.register_module(3, trip_form_view)

    # Index 4: Trip Viewer
    trip_viewer_view = TripViewerView()
    trip_viewer_presenter = TripViewerPresenter(trip_viewer_view, TripViewerModel(), api_service, event_bus)
    shell.register_module(4, trip_viewer_view)

    # Index 5: Profile
    profile_view = ProfileView()
    # חשוב: אנחנו מזריקים את ה-api_service למודל
    profile_model = ProfileModel(api_service) 
    profile_presenter = ProfilePresenter(profile_view, profile_model, event_bus)
    shell.register_module(5, profile_view)

    # 6. Global Navigation Logic
    def on_login_success(data):
        print(f"🎉 Login Success: {data.get('username')}")

        # The Shell is listening for "NAVIGATE". We tell it to go to Index 1 (Dashboard).
        event_bus.publish("NAVIGATE", {"index": 1})

    # Subscribe to the login event
    event_bus.subscribe("login_success", on_login_success)

    # 7. Launch
    shell.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()