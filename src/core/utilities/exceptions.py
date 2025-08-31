"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.core.utilities.exceptions import LocalizedException
from PySide6.QtWidgets import QApplication


class DownloadFailedError(LocalizedException):
    """
    Exception when download failed.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Download failed!")


class InstallationFailedError(LocalizedException):
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
