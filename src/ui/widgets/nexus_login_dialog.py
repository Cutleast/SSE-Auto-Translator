"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path
from threading import Event, Thread
from typing import ClassVar, Optional, override

from cutleast_core_lib.core.utilities.exe_info import get_current_path
from pydantic import BaseModel, SecretStr, ValidationError
from PySide6.QtCore import QDateTime, QProcess, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QPalette
from PySide6.QtNetwork import QNetworkCookie
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QWidget
from pywintypes import error as WindowsError

from core.translation_provider.nm_api.nm_api import NexusModsApi
from core.translation_provider.nm_api.web_session import NexusWebSession


class NexusLoginDialog(QDialog):
    """
    Obtains the API key and website session through one native WebView2 SSO login.
    """

    class __BrowserResult(BaseModel):
        """
        Private pipe response whose cookie values are redacted in representations.
        """

        cookies: list[SecretStr] = []
        user_agent: str = ""
        error: Optional[str] = None

    log: ClassVar[logging.Logger] = logging.getLogger("NexusLoginDialog")
    """Logs failure categories without authorization payloads or tracebacks."""

    __open_page = Signal(str)
    __authorized = Signal(str)
    __failed = Signal()

    __browser: QProcess
    __status_label: QLabel
    __cancel_button: QPushButton
    __cancel_event: Event
    __thread: Thread
    __pending_api_key: Optional[str]
    __session_timeout: QTimer
    __url: str
    __response: bytearray

    api_key: Optional[str]
    """The API key obtained by the completed login."""

    website_session: Optional[str]
    """The encrypted website session obtained by the same login."""

    @override
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Args:
            parent (Optional[QWidget], optional): Parent widget. Defaults to None.
        """

        super().__init__(parent)
        self.api_key = None
        self.website_session = None
        self.__pending_api_key = None
        self.__url = ""
        self.__response = bytearray()
        self.__cancel_event = Event()
        self.__init_ui()
        self.__cancel_button.clicked.connect(self.reject)
        self.__session_timeout = QTimer(self)
        self.__session_timeout.setSingleShot(True)
        self.__session_timeout.setInterval(30000)
        self.__session_timeout.timeout.connect(self.__show_error)
        self.__browser = QProcess(self)
        helper: Path = get_current_path() / "webview2-helper/bin/webview2-helper.exe"
        self.__browser.setProgram(str(helper))
        self.__browser.started.connect(self.__on_started)
        self.__browser.readyReadStandardOutput.connect(self.__read_response)
        self.__browser.errorOccurred.connect(lambda _: self.__show_error())
        self.__browser.finished.connect(self.__on_finished)
        self.__open_page.connect(self.__navigate)
        self.__authorized.connect(self.__finish_login)
        self.__failed.connect(self.__show_error)
        self.__thread = Thread(target=self.__run_sso, daemon=True)
        if helper.is_file():
            QTimer.singleShot(0, self.__thread.start)
        else:
            self.__show_error()
            self.__status_label.setText(
                self.tr(
                    "The native login helper is missing. Rebuild or reinstall SSE-AT."
                )
            )

    def __init_ui(self) -> None:
        """
        Creates the login status and cancellation control.
        """

        self.setWindowTitle(self.tr("Nexus Mods login"))
        self.setMinimumWidth(450)
        layout = QVBoxLayout(self)
        self.__status_label = QLabel(self.tr("Connecting to Nexus Mods..."))
        self.__status_label.setWordWrap(True)
        layout.addWidget(self.__status_label)
        self.__cancel_button = QPushButton(self.tr("Cancel"))
        layout.addWidget(self.__cancel_button)

    @Slot(str)
    def __navigate(self, url: str) -> None:
        """
        Starts the native browser without putting authorization data in arguments.

        Args:
            url (str): Authorization URL issued for this SSO attempt.
        """

        if not self.__cancel_event.is_set():
            self.__status_label.setText(
                self.tr("Sign in to Nexus Mods and authorize SSE-AT to continue.")
            )
            self.__url = url
            self.__browser.setArguments(self.__get_window_theme())
            self.__browser.start()

    def __get_window_theme(self) -> list[str]:
        """
        Passes the AT window's current theme colors to the native title bar.

        Returns:
            list[str]: Non-sensitive command-line arguments for the window theme.
        """

        source: QWidget = (self.parentWidget() or self).window()
        palette: QPalette = source.palette()
        background: QColor = palette.color(
            QPalette.ColorGroup.Active, QPalette.ColorRole.Window
        )
        foreground: QColor = palette.color(
            QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText
        )
        arguments: list[str] = ["--window-theme", str(int(background.lightness() < 128))]
        for color in (background, foreground):
            # Windows COLORREF uses 0x00BBGGRR rather than QColor's 0xAARRGGBB.
            arguments.append(str(color.red() | color.green() << 8 | color.blue() << 16))
        return arguments

    @Slot()
    def __on_started(self) -> None:
        """
        Sends navigation and any pending cookie request over the private input pipe.
        """

        if self.__cancel_event.is_set():
            self.__browser.closeWriteChannel()
            return
        self.__browser.write((self.__url + "\n").encode("utf8"))
        if self.__pending_api_key is not None:
            self.__browser.write(b"capture\n")

    def __run_sso(self) -> None:
        """
        Waits for SSO in a worker so the login browser remains responsive.
        """

        if self.__cancel_event.is_set():
            return
        try:
            api = NexusModsApi()
            key: str = api.get_sso_key(self.__open_page.emit, self.__cancel_event)
        except Exception as ex:  # noqa: BLE001 - Isolate the SSO worker from Qt.
            if not self.__cancel_event.is_set():
                self.log.error("Nexus Mods SSO failed: %s", type(ex).__name__)
                self.__failed.emit()
        else:
            if not self.__cancel_event.is_set():
                self.__authorized.emit(key)

    @Slot(str)
    def __finish_login(self, key: str) -> None:
        """
        Requests the website cookies after API authorization succeeds.

        Args:
            key (str): API key issued by the SSO server.
        """

        if self.__cancel_event.is_set():
            return
        self.__pending_api_key = key
        self.__status_label.setText(
            self.tr("Waiting for the Nexus Mods website session...")
        )
        self.__session_timeout.start()
        if self.__browser.state() == QProcess.ProcessState.Running:
            self.__browser.write(b"capture\n")

    @Slot()
    def __read_response(self) -> None:
        """
        Validates the helper response and encrypts cookies in the existing format.
        """

        self.__response.extend(self.__browser.readAllStandardOutput().data())
        if self.__cancel_event.is_set():
            self.__response.clear()
            return
        if len(self.__response) > 1024 * 1024:
            self.__show_error()
            return
        if b"\n" not in self.__response:
            return
        try:
            result = NexusLoginDialog.__BrowserResult.model_validate_json(
                bytes(self.__response)
            )
            self.__response.clear()
            if result.error is not None:
                self.__show_error()
                if result.error == "runtime_missing":
                    self.__status_label.setText(
                        self.tr(
                            "Microsoft Edge WebView2 Runtime is required. "
                            "Install the Evergreen Runtime from "
                            "https://developer.microsoft.com/microsoft-edge/webview2 "
                            "and try again."
                        )
                    )
                return
            cookies: list[QNetworkCookie] = [
                cookie
                for raw in result.cookies
                for cookie in QNetworkCookie.parseCookies(
                    raw.get_secret_value().encode("latin-1")
                )
                if cookie.domain() in {".nexusmods.com", "www.nexusmods.com"}
            ]
            key: Optional[str] = self.__pending_api_key
            if (
                key is None
                or not result.user_agent
                or not any(
                    cookie.name() == b"nexusmods_session"
                    and not cookie.value().isEmpty()
                    and (
                        cookie.isSessionCookie()
                        or cookie.expirationDate() > QDateTime.currentDateTimeUtc()
                    )
                    for cookie in cookies
                )
            ):
                self.__show_error()
                return
            self.website_session = NexusWebSession.encrypt(
                cookies, result.user_agent, key
            )
        except ValidationError, UnicodeError, WindowsError:
            self.__show_error()
            return
        self.api_key = key
        self.accept()

    @Slot()
    def __on_finished(self) -> None:
        """
        Drains the pipe before treating browser closure as cancellation.
        """

        self.__read_response()
        if not self.__cancel_event.is_set():
            self.reject()

    @Slot()
    def __show_error(self) -> None:
        """
        Keeps failures from being accepted and closes the browser through its pipe.
        """

        if self.__cancel_event.is_set():
            return
        self.__status_label.setText(
            self.tr("Nexus Mods login failed. Close this window and try again.")
        )
        self.__cancel_event.set()
        self.__session_timeout.stop()
        self.__pending_api_key = None
        self.__response.clear()
        self.__browser.closeWriteChannel()

    @override
    def done(self, result: int) -> None:
        """
        Cancels SSO and closes the helper before releasing the dialog.

        Args:
            result (int): Dialog result to return to the setup widget.
        """

        self.__cancel_event.set()
        self.__session_timeout.stop()
        self.__pending_api_key = None
        self.__response.clear()
        self.__browser.closeWriteChannel()
        if not self.__browser.waitForFinished(4000):
            self.__browser.kill()
            self.__browser.waitForFinished(1000)
        super().done(result)
