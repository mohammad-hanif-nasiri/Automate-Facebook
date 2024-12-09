class FBException(Exception):
    pass


class ShareLimitException(FBException):
    pass


class CommentLimitException(FBException):
    pass


class UserNotLoggedInException(Exception):
    """
    Exception raised when a user tries to perform an action without being logged in.
    """

    def __init__(self, message="User is not logged in. Please log in to continue."):
        self.message = message
        super().__init__(self.message)
