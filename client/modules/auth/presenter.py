class AuthPresenter:
    def __init__(self, view, api_service, event_bus):
        self.view = view
        self.api = api_service
        self.bus = event_bus

        # --- FIX: Match signal names to those in view.py ---
        self.view.login_signal.connect(self.handle_login)
        self.view.register_signal.connect(self.handle_register)

    def handle_login(self, username, password):
        print(f"🔑 Presenter: Login requested for {username}")
        
        # Call API (We assume api_service has a .login method)
        # If your API service is generic, we might need to adjust this later.
        try:
            response = self.api.login(username, password)
            
            status = response.get("status")
            if response and status in ["success", "valid"]:
                print("✅ Login Successful")
                # Navigate to the next screen using the Event Bus
                self.bus.publish("login_success", {"username": username})
            else:
                msg = response.get("detail") if response else "Unknown error"
                self.view.show_error(f"Login Failed: {msg}")
                
        except Exception as e:
            print(f"❌ Login Exception: {e}")
            self.view.show_error(f"Connection Error: {e}")

    def handle_register(self, username, password):
        print(f"📝 Presenter: Register requested for {username}")
        
        try:
            response = self.api.register(username, password)
            
            if response and response.get("status") == "success":
                self.view.show_success("Account created! Please login.")
            else:
                msg = response.get("detail") if response else "Unknown error"
                self.view.show_error(f"Registration Failed: {msg}")
                
        except Exception as e:
            print(f"❌ Register Exception: {e}")
            self.view.show_error(f"Connection Error: {e}")