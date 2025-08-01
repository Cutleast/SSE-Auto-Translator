"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtWidgets import QApplication

from core.utilities.exceptions import ExceptionBase


class ModManagerError(ExceptionBase):
    """
    Exception for general mod manager-related errors.
    """

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "A mod manager error occured!")


class InstanceNotFoundError(ModManagerError):
    """
    Exception when a mod instance does not exist.
    """

    def __init__(self, instance_name: str) -> None:
        super().__init__(instance_name)

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions", "The mod instance {0} could not be found!"
        )
