"""
Copyright (c) Cutleast
"""

from typing import Any, override

from PySide6.QtWidgets import QApplication

from core.utilities.exceptions import LocalizedException


class ProviderError(LocalizedException):
    """
    Base class for translation provider errors.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions", "A translation provider error occured!"
        )


class ModNotFoundError(ProviderError):
    """
    Exception when a requested mod could not be found.
    """

    def __init__(self, mod: str) -> None:
        super().__init__(mod)

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Mod '{0}' could not be found!")


class RequestError(ProviderError):
    """
    Exception when an API request failed or the API returned an unexpected response.
    """

    def __init__(self, request_url: str, *values: Any) -> None:
        super().__init__(request_url, *values)

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Request to '{0}' failed!")


class Non200HttpError(RequestError):
    """
    Exception when a request returned a non-200 HTTP status code.
    """

    def __init__(self, request_url: str, status_code: int) -> None:
        super().__init__(request_url, status_code)

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions", "Request to '{0}' failed with status code {1}!"
        )


class UnexpectedResponseError(RequestError):
    """
    Exception when a request returned an unexpected response that was failed to process.
    """

    def __init__(self, request_url: str, response_text: str) -> None:
        super().__init__(request_url, response_text)

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions",
            "Request to '{0}' returned an unexpected response!\nResponse: {1}",
        )


class ApiKeyInvalidError(RequestError):
    """
    Exception when api key is invalid for attempted request.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions", "Key invalid for request! Request url: {0}"
        )


class ApiPermissionError(RequestError):
    """
    Exception when request is blocked by NM because of missing permissions.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions", "No Permission for request! Request url: {0}"
        )


class ApiExpiredError(RequestError):
    """
    Exception when request has expired.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions", "Request has expired! Request url: {0}"
        )


class ApiInvalidServerError(RequestError):
    """
    Exception when specified server is invalid.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions", "Server is invalid! Request url: {0}"
        )


class ApiNoServerAvailableError(RequestError):
    """
    Exception when there is no server available for the request.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions", "No server available for the request! Request url: {0}"
        )


class ApiLimitReachedError(RequestError):
    """
    Exception when request has reached limit.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions", "API Request Limit reached! Request url: {0}"
        )
