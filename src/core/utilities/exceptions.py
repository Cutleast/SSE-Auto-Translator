"""
Copyright (c) Cutleast
"""

from abc import abstractmethod
from typing import Callable, Optional, ParamSpec, TypeVar, override

from PySide6.QtWidgets import QApplication

# Nuitka doesn't support the new syntax, yet
T = TypeVar("T")
P = ParamSpec("P")


class ExceptionBase(Exception):
    """
    Base Exception class for localized exceptions.
    """

    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or self.getLocalizedMessage())

    @abstractmethod
    def getLocalizedMessage(self) -> str:
        """
        Returns localised message

        Returns:
            str: Localised message
        """

    @classmethod
    def wrap(cls, func_or_meth: Callable[P, T]) -> Callable[P, T]:
        """
        Wraps function or method in a try-except-block
        that raises an exception of this type.

        Args:
            func_or_meth (F): Function or method

        Returns:
            F: Wrapped function or method
        """

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func_or_meth(*args, **kwargs)
            except Exception as e:
                raise cls() from e

        return wrapper


class ApiException(ExceptionBase):
    """
    Base Exception class for API errors.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "An API error occured!")


class ApiKeyInvalidError(ApiException):
    """
    Exception when api key is invalid for attempted request.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Key invalid for request!")


class ApiPermissionError(ApiException):
    """
    Exception when request is blocked by NM because of missing permissions.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "No Permission for request!")


class ApiExpiredError(ApiException):
    """
    Exception when request has expired.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Request has expired!")


class ApiInvalidServerError(ApiException):
    """
    Exception when specified server is invalid. (Downloader)
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Server is invalid!")


class ApiLimitReachedError(ApiException):
    """
    Exception when request has reached limit.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "API Request Limit reached!")


class DownloadFailedError(ExceptionBase):
    """
    Exception when download failed.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Download failed!")


class InstallationFailedError(ExceptionBase):
    """
    Exception when installation failed.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Installation failed!")


class MappingFailedError(InstallationFailedError):
    """
    Exception when the translation could not be mapped to the original mod.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions",
            "Mapping failed! Translation does not contain any matching strings!",
        )


class NoOriginalModFound(InstallationFailedError):
    """
    Exception when no original mod could be found for the translation.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions", "No original mod found for the translation!"
        )
