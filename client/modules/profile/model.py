import json
import os

class ProfileModel:
    def __init__(self, api_service):
        self.api = api_service
        # מבנה הנתונים המלא כולל נתוני הגרף
        self.user_stats = {
            "username": "Guest",
            "email": "guest@example.com",
            "trip_count": 0,
            "total_budget": 0,
            "days_traveled": 0,
            "level_title": "Novice Explorer",
            "level_progress": 0,
            "next_level_hint": "Plan your first trip!",
            "last_trip_dest": "-",
            # שדה ייעודי לנתוני הגרף
            "chart_data": {"labels": [], "values": []},
            # העדפות
            "preferences": {
                "pace": 50, 
                "luxury": 50, 
                "foodie": False, 
                "nature": False, 
                "history": False, 
                "shopping": False, 
                "nightlife": False
            }
        }

    # --- פונקציות עזר (פרטיות) ---
    def _parse_money(self, val):
        """מנקה מחרוזות כמו '$1,200' למספר 1200"""
        try:
            raw = str(val).replace("$", "").replace(",", "").strip()
            return int(float(raw))
        except:
            return 0

    def change_password(self, username, old_pass, new_pass):
        """שולח בקשה לשרת לשינוי סיסמה עם אימות"""
        # בדיקות מקומיות בסיסיות
        if not old_pass:
            return False, "Enter old password"
        if not new_pass or new_pass.strip() == "":
            return False, "New password cannot be empty"
            
        try:
            payload = {
                "username": username,
                "old_password": old_pass,
                "new_password": new_pass
            }
            
            # שליחה לשרת
            # ה-APIService בדרך כלל מטפל בשגיאות ומחזיר None במקרה של כישלון, 
            # או זורק שגיאה אם מוגדר אחרת. נניח כאן שהשרת מחזיר שגיאה ב-JSON אם נכשל.
            response = self.api.post("/users/change_password", payload)
            
            if response and response.get("status") == "password_updated":
                return True, "Password changed successfully!"
            
            # אם הגיע לכאן, כנראה שהייתה שגיאה שה-API תפס (כמו 401)
            # במימוש הנוכחי של APIService, אם יש שגיאת HTTP הוא לרוב מדפיס לוג ומחזיר None.
            # כדי לתת פידבק מדויק יותר, נניח שאם חזר None זה נכשל.
            return False, "Incorrect old password or server error"

        except Exception as e:
            return False, str(e)

    def _calculate_level(self, trips):
        if trips == 0: return "Rookie", 0, "Book a trip!"
        if trips < 3: return "Explorer", int((trips/3)*100), "3 trips for next rank"
        if trips < 10: return "Globetrotter", int((trips/10)*100), "10 trips for Legend"
        return "Legend", 100, "Max Level"

    def logout(self):
        pass

    def fetch_user_data(self, username):
        """טוען נתונים מהשרת (MongoDB) וממזג עם היסטוריית טיולים"""
        if not username:
            return self.user_stats

        try:
            # 1. שליפת פרופיל מהשרת (דרך ה-Controller שיצרנו)
            profile_resp = self.api.post("/users/profile", {"username": username}) or {}
            
            # 2. שליפת היסטוריית טיולים
            history_resp = self.api.post("/trips/history", {"username": username})
            trips = history_resp.get("trips", []) if history_resp else []

            # --- חישוב סטטיסטיקות ---
            trip_count = len(trips)
            total_budget = 0
            total_days = 0
            
            chart_labels = []
            chart_values = []
            recent_trips = trips[-5:] if len(trips) > 5 else trips
            
            for t in recent_trips:
                dest = t.get("destination", "Unknown")
                if len(dest) > 12: dest = dest[:10] + ".."
                chart_labels.append(dest)
                chart_values.append(self._parse_money(t.get("budget")))

            for t in trips:
                total_budget += self._parse_money(t.get("budget"))
                total_days += int(t.get("duration", 0))
            
            level_title, level_progress, next_level_hint = self._calculate_level(trip_count)
            last_dest = trips[-1].get("destination") if trips else "-"

            # --- מיזוג הנתונים ---
            self.user_stats.update({
                "username": username,
                "trip_count": trip_count,
                "total_budget": total_budget,
                "days_traveled": total_days,
                "level_title": level_title,
                "level_progress": level_progress,
                "next_level_hint": next_level_hint,
                "last_trip_dest": last_dest,
                "chart_data": {"labels": chart_labels, "values": chart_values},
                
                # טעינת נתונים שהגיעו מה-DB
                "email": profile_resp.get("email", self.user_stats["email"]),
                # אם הגיעו העדפות מהשרת נשתמש בהן, אחרת נשמור על ברירת המחדל
                "preferences": profile_resp.get("preferences") or self.user_stats["preferences"]
            })
            
            return self.user_stats

        except Exception as e:
            print(f"❌ Error in ProfileModel: {e}")
            return self.user_stats

    def save_profile_data(self, username, data_type, new_data):
        """שמירה לשרת (MongoDB)"""
        try:
            payload = {"username": username}
            
            if data_type == "preferences":
                payload["preferences"] = new_data
                self.user_stats["preferences"] = new_data # עדכון לוקאלי מיידי
                
            elif data_type == "identity":
                payload["email"] = new_data.get("email")
                self.user_stats["email"] = new_data.get("email")

            # שליחה לשרת
            resp = self.api.post("/users/update", payload)
            
            if resp and resp.get("status") == "updated":
                return True, "Saved to Cloud"
            else:
                return False, "Failed to save"
                
        except Exception as e:
            return False, str(e)