class DashboardModel:
    def __init__(self):
        self._username = "Traveler"

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        self._username = value