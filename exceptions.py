class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class MarvinDefaultError(Error):
    """
    Raise when  the configuration file
    Attributes:
        msg  -- explanation of the error
    """

    def __init__(self, msg):
        self.msg = msg


class MissingConfigParameterError(MarvinDefaultError):
    pass


class MissingValueError(MarvinDefaultError):
    pass


class NoDraftExistError(MarvinDefaultError):
    pass
