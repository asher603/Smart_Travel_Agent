import json

class ProfileModel:
    def __init__(self, api_service):
        self.api = api_service
        self.current_username = None # שומרים כאן את מי שמחובר כרגע
        self.user_data = {}

    def set_current_user(self, username):
        """פונקציה שנקראת מיד אחרי לוגין כדי לקבוע מי המשתמש"""
        self.current_username = username
        self.user_data["username"] = username

    def fetch_user_data(self):
        """ניגש לשרת ומושך את הנתונים העדכניים של המשתמש הנוכחי"""
        if not self.current_username:
            return {"username": "Guest", "email": ""}

        try:
            # שליחת בקשה לשרת לקבלת פרופיל מלא
            # אנו מניחים שיש endpoint בשרת שמקבל username ומחזיר פרטים
            response = self.api.post("/users/profile", {"username": self.current_username})
            
            email = ""
            if response and "email" in response:
                email = response["email"]

            # עדכון הזיכרון הלוקאלי עם המידע הטרי מהשרת
            self.user_data = {
                "username": self.current_username,
                "email": email
            }
            return self.user_data

        except Exception as e:
            print(f"❌ Error fetching profile: {e}")
            # במקרה שגיאה נחזיר לפחות את השם שיש לנו
            return {"username": self.current_username, "email": ""}

    def save_profile_data(self, new_email):
        """שמירת האימייל לשרת"""
        if not self.current_username:
            return False, "No user logged in"

        try:
            payload = {
                "username": self.current_username,
                "email": new_email
            }
            
            # עדכון בשרת
            resp = self.api.post("/users/update", payload)
            
            # --- הוספתי את השורה הזו לדיבאג ---
            print(f"DEBUG: Server response for update: {resp}") 
            # ----------------------------------

            if resp and resp.get("status") == "updated":
                self.user_data["email"] = new_email
                return True, "Email updated successfully"
            else:
                return False, "Failed to update email"
                
        except Exception as e:
            print(f"Error saving profile: {e}") # הדפסת שגיאה ברורה יותר
            return False, str(e)

    def change_password(self, old_pass, new_pass):
        """שינוי סיסמה מול השרת"""
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
        """איפוס נתונים ביציאה"""
        self.current_username = None
        self.user_data = {}