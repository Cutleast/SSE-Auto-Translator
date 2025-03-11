"""
Copyright (c) Cutleast
"""

from abc import abstractmethod
from typing import Any, Callable, ParamSpec, TypeVar, override

from PySide6.QtWidgets import QApplication

# Nuitka doesn't support the new syntax, yet
T = TypeVar("T")
P = ParamSpec("P")


class ExceptionBase(Exception):
    """
    Base Exception class for localized exceptions.
    """

    def __init__(self, *values: Any) -> None:
        if self.getLocalizedMessage():
            super().__init__(self.getLocalizedMessage().format(*values))
        else:
            super().__init__(*values)

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
