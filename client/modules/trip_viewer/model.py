class TripViewerModel:
    def __init__(self):
        self.username = ""
        self.trip_id = None
        self.current_plan = {}
        self.history_state = []
        self.version_counter = 0
        self.current_context = ""