"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Callable, Generic, TypeVar

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QWidget

T = TypeVar("T")


class Thread(QThread, Generic[T]):
    """
    Adapted QThread with a generic return type.
    """

    __target: Callable[[], T]
    __return_result: T | Exception

    def __init__(
        self,
        target: Callable[[], T],
        name: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.__target = target

        if name is not None:
            self.setObjectName(name)

    def run(self) -> None:
        """
        Runs the target function, storing its return value or an exception.
        """

        try:
            self.__return_result = self.__target()
        except Exception as ex:
            self.__return_result = ex

    def get_result(self) -> T | Exception:
        """
        Returns the return value of the target function or an exception.

        Returns:
            T | Exception: Return value of the target function or an exception
        """

        return self.__return_result
