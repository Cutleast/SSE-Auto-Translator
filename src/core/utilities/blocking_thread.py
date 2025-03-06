"""
Copyright (c) Cutleast
"""

from typing import Callable, Generic, TypeVar, override

from PySide6.QtCore import QEventLoop, QThread
from PySide6.QtWidgets import QWidget

T = TypeVar("T")


class BlockingThread(QThread, Generic[T]):
    """
    QThread that blocks MainThread execution while keeping the Qt application responsive.
    """

    __target: Callable[[], T]
    __event_loop: QEventLoop

    __return_result: T

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

        self.__event_loop = QEventLoop(self)
        self.finished.connect(self.__event_loop.quit)

    def start(self) -> T:  # type: ignore[override]
        """
        Starts the thread and waits for it to finish, blocking the execution of MainThread,
        while keeping the Qt application responsive.

        Returns:
            The return value of the target function.
        """

        super().start()

        self.__event_loop.exec()

        return self.__return_result

    @override
    def run(self) -> None:
        """
        Runs the target function, storing its return value.

        The return value can be accessed with `start()`.
        """

        self.__return_result = self.__target()
