class FailedConnectionError(Exception):
    """Raise for failed connection or timeout"""


class AuthenticationError(Exception):
    """Raise for authentication error"""


class APIError(Exception):
    """Raise for API error"""


class APIInvalidResponse(APIError):
    """Raise for invalid API response"""

    def __init__(self, reason: str | None = None):
        self.msg = "Failed to validate API response"
        self.reason = reason
        if self.reason:
            self.msg = f"{self.msg}: {self.reason}"
        super().__init__(self.msg)
