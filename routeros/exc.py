class TrapError(Exception):
    """
    Exception raised when !trap is received!
    """
    pass


class FatalError(Exception):
    """
    Exception raised when !fatal is received!
    """
    pass


class ConnectionError(Exception):
    """
    Exception raised when is not possible to connect to routerOS!
    """
    pass
