from datetime import date

class TripFormModel:
    def __init__(self):
        self.username = "Guest"
        self.destination = ""
        self.origin = ""
        self.budget = 0
        self.currency = "USD"
        self.interests = ""
        self.start_date = date.today()
        self.end_date = date.today()
        self.email = None

    def is_valid(self):
        # Basic business logic validation
        if not self.destination or not self.origin:
            return False, "Destination and Origin are required."
        if self.budget <= 0:
            return False, "Please enter a valid budget."
        if self.start_date >= self.end_date:
            return False, "End date must be after start date."
        return True, ""