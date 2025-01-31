class FailedConnectionError(Exception):
    """Raise for failed connection to miner"""


class AuthenticationError(Exception):
    """Raise for authentication failure to miner"""


class MissingAPIKeyError(Exception):
    """Raise for missing API key"""