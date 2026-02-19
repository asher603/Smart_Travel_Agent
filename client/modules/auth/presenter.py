from core.security import validate_and_protect

class AuthPresenter:
    def __init__(self, view, api_service, event_bus):
        self.view = view
        self.api = api_service
        self.bus = event_bus

        # --- FIX: Match signal names to those in view.py ---
        self.view.login_signal.connect(self.handle_login)
        self.view.register_signal.connect(self.handle_register)
        
        # 🔄 Subscribe to logout event to reset the form
        self.bus.subscribe("NAVIGATE", self.on_navigate)

    def on_navigate(self, data):
        """Reset form when navigating back to login screen"""
        if data.get("index") == 0:
            self.view.reset_form()

    def handle_login(self, username, password):
        print(f"🔑 Presenter: Login requested for {username}")
        
        # 🛡️ SECURITY CHECK
        if not validate_and_protect(username=username, password=password):
            return
        
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
        
        # SECURITY CHECK (Prompt Injection Prevention)
        if not validate_and_protect(username=username, password=password):
            return
            
        # PASSWORD COMPLEXITY CHECK
        has_min_length = len(password) >= 8
        has_letter = any(c.isalpha() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_min_length and has_letter and has_digit):
            self.view.show_error("Password must be at least 8 characters and include both letters and numbers.")
            return
        
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