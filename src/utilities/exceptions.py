"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""


class GeneralException(Exception):
    """
    General Exception class.
    """

    text: str = None  # Text for traceback
    id: str = None  # Localisation id

    def __init__(self, *args: object):
        super().__init__(self.text, *args)


class ApiException(Exception):
    """
    General Exception class for API errors.
    """

    text = "Request failed"
    id = "api_error"


class ApiKeyInvalidError(ApiException):
    """
    Exception when api key is invalid for attempted request.
    """

    text = "Key invalid for request"
    id = "key_invalid"


class ApiPermissionError(ApiException):
    """
    Exception when request is blocked by NM because of missing permissions.
    """

    text = "No Permission for request"
    id = "no_permission"


class ApiExpiredError(ApiException):
    """
    Exception when request has expired.
    """

    text = "Request has expired"
    id = "request_expired"


class ApiInvalidServerError(ApiException):
    """
    Exception when specified server is invalid. (Downloader)
    """

    text = "Server is invalid"
    id = "server_invalid"


class ApiLimitReachedError(ApiException):
    """
    Exception when request has reached limit.
    """

    text = "API Request Limit reached"
    id = "limit_reached"

