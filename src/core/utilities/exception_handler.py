"""
Copyright (c) Cutleast
"""

import logging
import sys
from traceback import format_exception
from types import TracebackType
from typing import Callable
from winsound import MessageBeep as alert

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication

from ui.widgets.error_dialog import ErrorDialog


class ExceptionHandler(QObject):
    """
    Redirects uncatched exceptions to an ErrorDialog instead of crashing the entire app.
    """

    log: logging.Logger = logging.getLogger("ExceptionHandler")
    __sys_excepthook: (
        Callable[[type[BaseException], BaseException, TracebackType | None], None]
        | None
    ) = None

    __parent: QApplication

    def __init__(self, parent: QApplication):
        super().__init__(parent)

        self.__parent = parent

        self.bind_hook()

    def bind_hook(self) -> None:
        """
        Binds ExceptionHandler to `sys.excepthook`.
        """

        if self.__sys_excepthook is None:
            self.__sys_excepthook = sys.excepthook
            sys.excepthook = self.__exception_hook

    def unbind_hook(self) -> None:
        """
        Unbinds ExceptionHandler and restores original `sys.excepthook`.
        """

        if self.__sys_excepthook is not None:
            sys.excepthook = self.__sys_excepthook
            self.__sys_excepthook = None

    def __exception_hook(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None:
        """
        Redirects uncatched exceptions and shows them in an ErrorDialog.
        """

        # Pass through if exception is KeyboardInterrupt (Ctrl + C)
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        traceback = "".join(format_exception(exc_type, exc_value, exc_traceback))
        self.log.critical("An uncaught exception occured:\n" + traceback)

        error_message = self.tr("An unexpected error occured: ") + str(exc_value)
        detailed_msg = traceback

        error_dialog = ErrorDialog(
            parent=self.__parent.activeModalWidget(),
            title=self.tr("Error"),
            text=error_message,
            details=detailed_msg,
        )

        # Play system alarm sound
        alert()

        choice = error_dialog.exec()

        if choice == ErrorDialog.StandardButton.No:
            self.__parent.exit()
