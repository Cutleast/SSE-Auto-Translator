"""
Copyright (c) Cutleast
"""

from abc import abstractmethod

from PySide6.QtWidgets import QApplication


class ExceptionBase(Exception):
    """
    Base Exception class for localized exceptions.
    """

    @abstractmethod
    def getLocalizedMessage(self) -> str:
        """
        Returns localised message

        Returns:
            str: Localised message
        """

    def __str__(self) -> str:
        return self.getLocalizedMessage()

    def __repr__(self) -> str:
        return self.getLocalizedMessage()


class ApiException(ExceptionBase):
    """
    Base Exception class for API errors.
    """

    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "An API error occured!")


class ApiKeyInvalidError(ApiException):
    """
    Exception when api key is invalid for attempted request.
    """

    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Key invalid for request!")


class ApiPermissionError(ApiException):
    """
    Exception when request is blocked by NM because of missing permissions.
    """

    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "No Permission for request!")


class ApiExpiredError(ApiException):
    """
    Exception when request has expired.
    """

    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Request has expired!")


class ApiInvalidServerError(ApiException):
    """
    Exception when specified server is invalid. (Downloader)
    """

    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Server is invalid!")


class ApiLimitReachedError(ApiException):
    """
    Exception when request has reached limit.
    """

    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "API Request Limit reached!")


class DownloadFailedError(ExceptionBase):
    """
    Exception when download failed.
    """

    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Download failed!")


class InstallationFailedError(ExceptionBase):
    """
    Exception when installation failed.
    """

    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Installation failed!")


class MappingFailedError(InstallationFailedError):
    """
    Exception when the translation could not be mapped to the original mod.
    """

    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions",
            "Mapping failed! Translation does not contain any matching strings!",
        )


class NoOriginalModFound(InstallationFailedError):
    """
    Exception when no original mod could be found for the translation.
    """

    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions", "No original mod found for the translation!"
        )
