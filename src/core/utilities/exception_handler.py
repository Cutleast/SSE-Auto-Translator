"""
Copyright (c) Cutleast
"""

import json
import logging
import re
import sys
from pathlib import Path
from traceback import format_exception
from types import FrameType, TracebackType
from typing import Any, Callable
from winsound import MessageBeep as alert

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication

from app_context import AppContext
from ui.widgets.error_dialog import ErrorDialog
from ui.widgets.loading_dialog import LoadingDialog

from .serializer import Serializer


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

        traceback: str = "".join(format_exception(exc_type, exc_value, exc_traceback))
        self.log.critical("An uncaught exception occured:\n" + traceback)

        error_message: str = self.tr("An unexpected error occured: ") + str(exc_value)

        error_dialog = ErrorDialog(
            parent=self.__parent.activeModalWidget(),
            title=self.tr("Error"),
            text=error_message,
            details=traceback,
            dump=True,
        )

        # TODO: Add messagebox after dump is done
        def dump(ldialog: LoadingDialog) -> None:
            ldialog.updateProgress(text1=self.tr("Dumping application state..."))
            self.dump_state_to_file(exc_type, exc_value, exc_traceback)

        error_dialog.dump_signal.connect(
            lambda: LoadingDialog.run_callable(self.__parent.activeModalWidget(), dump)
        )

        # Play system alarm sound
        alert()

        choice = error_dialog.exec()

        if choice == ErrorDialog.DialogCode.Accepted:
            self.__parent.exit()

    def dump_state_to_file(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None:
        """
        Dumps the given application state to a JSON file.
        """

        from core.archiver.archive import Archive

        dump_file_path = Path("app_state_dump.json")
        log_file_path = Path("SSE_AT.log")
        archive_file_path: Path = dump_file_path.with_suffix(".7z")

        self.log.info(f"Dumping application state to '{archive_file_path}'...")

        try:
            # Capture the local variables from the frame where the exception occurred
            locals_from_exception: dict[str, Any] = {}
            frame_locals: dict[str, dict[str, Any]] = {}
            if exc_traceback is not None:
                # Walk through the traceback to find the last frame
                # (where the exception was raised)
                tb: TracebackType = exc_traceback
                frame: FrameType = tb.tb_frame
                while tb.tb_next:
                    tb = tb.tb_next
                    frame = tb.tb_frame
                    frame_locals[tb.tb_frame.f_code.co_qualname] = tb.tb_frame.f_locals
                # Get local variables from the frame
                locals_from_exception = frame.f_locals

            _locals: dict[str, Any] = {
                k: v
                for k, v in locals_from_exception.items()
                if all(re.match(p, k) is None for p in Serializer.BLACKLIST_PATTERNS)
            }

            traceback: str = "".join(
                format_exception(exc_type, exc_value, exc_traceback)
            )

            # Combine state information
            state: dict[str, Any] = {
                "exception": {
                    "type": str(exc_type),
                    "message": str(exc_value),
                    "traceback": traceback.splitlines(),
                },
                "locals": _locals,
                "app": self.__parent,
                "frames": frame_locals,
            }

            with dump_file_path.open("w", encoding="utf8") as dump_file:
                json.dump(
                    Serializer.make_serializable(state),
                    dump_file,
                    indent=4,
                    ensure_ascii=False,
                )

            Serializer.clear()

            # Write log to a temporary log file
            with log_file_path.open("w", encoding="utf8") as log_file:
                log_file.write(AppContext.get_app().logger.get_content())

            # Pack the dump file into a 7zip archive
            archive: Archive = Archive.load_archive(archive_file_path)
            archive.add_files([dump_file_path, log_file_path])

            self.log.info("Application state dumped.")
        except Exception as ex:
            self.log.error(f"Failed to dump application state: {ex}", exc_info=ex)
        finally:
            dump_file_path.unlink(missing_ok=True)
            log_file_path.unlink(missing_ok=True)
