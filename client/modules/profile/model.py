import json

class ProfileModel:
    def __init__(self, api_service):
        self.api = api_service
        self.current_username = None  # Store currently logged in user
        self.user_data = {}

    def set_current_user(self, username):
        """Called immediately after login to set current user"""
        self.current_username = username
        self.user_data["username"] = username

    def fetch_user_data(self):
        """Fetch current user's data from server"""
        if not self.current_username:
            return {"username": "Guest", "email": ""}

        try:
            # Send request to server for full profile
            # Assumes endpoint exists that receives username and returns details
            response = self.api.post("/users/profile", {"username": self.current_username})
            
            email = ""
            if response and "email" in response:
                email = response["email"]

            # Update local memory with fresh server data
            self.user_data = {
                "username": self.current_username,
                "email": email
            }
            return self.user_data

        except Exception as e:
            print(f"❌ Error fetching profile: {e}")
            # On error, return at least the name we have
            return {"username": self.current_username, "email": ""}

    def save_profile_data(self, new_email):
        """Save email to server"""
        if not self.current_username:
            return False, "No user logged in"

        try:
            payload = {
                "username": self.current_username,
                "email": new_email
            }
            
            # Update on server
            resp = self.api.post("/users/update", payload)
            
            # Debug logging for server response
            print(f"DEBUG: Server response for update: {resp}") 
            # ----------------------------------

            if resp and resp.get("status") == "updated":
                self.user_data["email"] = new_email
                return True, "Email updated successfully"
            else:
                return False, "Failed to update email"
                
        except Exception as e:
            print(f"Error saving profile: {e}")  # Clearer error output
            return False, str(e)

    def change_password(self, old_pass, new_pass):
        """Change password via server"""
        if not self.current_username:
            return False, "No user logged in"
            
        try:
            payload = {
                "username": self.current_username,
                "old_password": old_pass,
                "new_password": new_pass
            }
            
            response = self.api.post("/users/change_password", payload)
            
            if response and response.get("status") == "password_updated":
                return True, "Password changed successfully!"
            
            return False, "Incorrect old password or server error"

        except Exception as e:
            return False, str(e)

    def logout(self):
        """Reset data on logout"""
        self.current_username = None
        self.user_data = {}