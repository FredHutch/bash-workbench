import datetime

class Timestamp():
    """Encode / decode a date and time to / from string format."""

    def __init__(self, fmt="%Y-%m-%d %H:%M:%S %Z"):
        
        self.fmt = fmt

    def encode(self):
        """Return a string representation of the current date and time."""

        # Current date and time
        now = datetime.datetime.now(datetime.timezone.utc)

        # Return a string formatted using the pattern shown above
        return now.strftime(self.fmt)

    def decode(self, timestamp_str):
        """Return the date and time represented by a string."""

        return datetime.strptime(timestamp_str, self.fmt)