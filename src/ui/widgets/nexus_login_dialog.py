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

    class __BrowserResult(BaseModel, frozen=True):
        """
        Private pipe response whose cookie values are redacted in representations.
        """

        cookies: list[SecretStr] = []
        """The raw `Set-Cookie` values of the browser's cookies."""

        user_agent: str = ""
        """The user agent of the browser."""

        error: Optional[str] = None
        """The error category reported by the helper, if any."""

    __HELPER_PATH: Path = Path("webview2-helper") / "bin" / "webview2-helper.exe"
    """The path to the native login helper, relative to the current path."""

    __SESSION_TIMEOUT: int = 30000
    """The time in milliseconds to wait for the website session after authorization."""

    __HELPER_SHUTDOWN_TIMEOUT: int = 4000
    """The time in milliseconds to wait for the helper to close itself."""

    __HELPER_KILL_TIMEOUT: int = 1000
    """The time in milliseconds to wait for the helper after killing it."""

    __MAX_RESPONSE_SIZE: int = 1024 * 1024
    """The maximum size in bytes of a helper response."""

    __DARK_THEME_LIGHTNESS: int = 128
    """The window lightness below which the native title bar uses the dark theme."""

    __NEXUS_COOKIE_DOMAINS: set[str] = {".nexusmods.com", "www.nexusmods.com"}
    """The cookie domains that belong to the Nexus Mods website."""

    log: ClassVar[logging.Logger] = logging.getLogger("NexusLoginDialog")
    """Logs failure categories without authorization payloads or tracebacks."""

    __open_page = Signal(str)
    """
    Requests navigation to the SSO authorization page on the GUI thread.

    Args:
        str: Authorization URL issued for this SSO attempt.
    """

    __authorized = Signal(str)
    """
    Delivers the API key issued by the SSO server to the GUI thread.

    Args:
        str: API key issued by the SSO server.
    """

    __failed = Signal()
    """Reports an SSO failure without exposing authorization data."""

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

        self.__session_timeout = QTimer(self)
        self.__session_timeout.setSingleShot(True)
        self.__session_timeout.setInterval(NexusLoginDialog.__SESSION_TIMEOUT)

        helper_path: Path = get_current_path() / NexusLoginDialog.__HELPER_PATH
        self.__browser = QProcess(self)
        self.__browser.setProgram(str(helper_path))

        self.__thread = Thread(target=self.__run_sso, daemon=True)

        self.__cancel_button.clicked.connect(self.reject)
        self.__session_timeout.timeout.connect(self.__show_error)
        self.__browser.started.connect(self.__on_started)
        self.__browser.readyReadStandardOutput.connect(self.__read_response)
        self.__browser.errorOccurred.connect(lambda _: self.__show_error())
        self.__browser.finished.connect(self.__on_finished)
        self.__open_page.connect(self.__navigate)
        self.__authorized.connect(self.__finish_login)
        self.__failed.connect(self.__show_error)

        if helper_path.is_file():
            QTimer.singleShot(0, self.__thread.start)
        else:
            self.__fail(self.tr("The native login helper is missing. Reinstall SSE-AT."))

    def __init_ui(self) -> None:
        """
        Creates the login status and cancellation control.
        """

        self.setWindowTitle(self.tr("Nexus Mods login"))
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)

        self.__status_label = QLabel(self.tr("Connecting to Nexus Mods..."))
        self.__status_label.setWordWrap(True)
        self.__status_label.setOpenExternalLinks(True)
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

        if self.__cancel_event.is_set():
            return

        self.__status_label.setText(
            self.tr("Sign in to Nexus Mods and authorize SSE-AT to continue.")
        )
        self.__url = url
        self.__browser.setArguments(self.__get_window_theme_arguments())
        self.__browser.start()

    def __get_window_theme_arguments(self) -> list[str]:
        """
        Builds the arguments that pass the current window theme to the native title
        bar.

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
        dark_theme: bool = (
            background.lightness() < NexusLoginDialog.__DARK_THEME_LIGHTNESS
        )

        return [
            "--window-theme",
            str(int(dark_theme)),
            str(NexusLoginDialog.__to_colorref(background)),
            str(NexusLoginDialog.__to_colorref(foreground)),
        ]

    @staticmethod
    def __to_colorref(color: QColor) -> int:
        """
        Converts a color to a Windows COLORREF, which uses 0x00BBGGRR rather than
        QColor's 0xAARRGGBB.

        Args:
            color (QColor): Color to convert.

        Returns:
            int: COLORREF value of the color.
        """

        return color.red() | (color.green() << 8) | (color.blue() << 16)

    @Slot()
    def __on_started(self) -> None:
        """
        Sends navigation and any pending cookie request over the private input pipe.
        """

        if self.__cancel_event.is_set():
            self.__browser.closeWriteChannel()
            return

        self.__browser.write(f"{self.__url}\n".encode())
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
        Buffers the helper output until a complete response line can be validated.
        """

        self.__response.extend(self.__browser.readAllStandardOutput().data())
        if self.__cancel_event.is_set():
            self.__response.clear()
            return

        if len(self.__response) > NexusLoginDialog.__MAX_RESPONSE_SIZE:
            self.__show_error()
            return

        if b"\n" not in self.__response:
            return

        try:
            result: NexusLoginDialog.__BrowserResult = (
                NexusLoginDialog.__BrowserResult.model_validate_json(
                    bytes(self.__response)
                )
            )
        except ValidationError:
            self.__show_error()
            return
        finally:
            self.__response.clear()

        if result.error == "runtime_missing":
            self.__fail(
                self.tr(
                    "Microsoft Edge WebView2 Runtime is required. "
                    "Install the Evergreen Runtime from "
                    "https://developer.microsoft.com/microsoft-edge/webview2 "
                    "and try again."
                )
            )
        elif result.error is not None:
            self.__show_error()
        else:
            self.__complete_login(result.cookies, result.user_agent)

    def __complete_login(self, raw_cookies: list[SecretStr], user_agent: str) -> None:
        """
        Encrypts the website cookies in the existing format and accepts the login once
        they contain a valid website session.

        Args:
            raw_cookies (list[SecretStr]): Raw `Set-Cookie` values from the helper.
            user_agent (str): User agent of the helper's browser.
        """

        key: Optional[str] = self.__pending_api_key
        try:
            cookies: list[QNetworkCookie] = NexusLoginDialog.__parse_cookies(raw_cookies)
        except UnicodeError:
            self.__show_error()
            return

        if (
            key is None
            or not user_agent
            or not NexusLoginDialog.__has_valid_session(cookies)
        ):
            self.__show_error()
            return

        try:
            self.website_session = NexusWebSession.encrypt(cookies, user_agent, key)
        except WindowsError:
            self.__show_error()
            return

        self.api_key = key
        self.accept()

    @staticmethod
    def __parse_cookies(raw_cookies: list[SecretStr]) -> list[QNetworkCookie]:
        """
        Parses the raw cookies and keeps only those belonging to the Nexus website.

        Args:
            raw_cookies (list[SecretStr]): Raw `Set-Cookie` values from the helper.

        Returns:
            list[QNetworkCookie]: Parsed Nexus website cookies.

        Raises:
            UnicodeError: When a cookie value is not representable in Latin-1.
        """

        return [
            cookie
            for raw_cookie in raw_cookies
            for cookie in QNetworkCookie.parseCookies(
                raw_cookie.get_secret_value().encode("latin-1")
            )
            if cookie.domain() in NexusLoginDialog.__NEXUS_COOKIE_DOMAINS
        ]

    @staticmethod
    def __has_valid_session(cookies: list[QNetworkCookie]) -> bool:
        """
        Checks whether the cookies contain a non-empty, unexpired website session.

        Args:
            cookies (list[QNetworkCookie]): Nexus website cookies.

        Returns:
            bool: Whether a valid website session cookie is present.
        """

        return any(
            cookie.name() == b"nexusmods_session"
            and not cookie.value().isEmpty()
            and (
                cookie.isSessionCookie()
                or cookie.expirationDate() > QDateTime.currentDateTimeUtc()
            )
            for cookie in cookies
        )

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
        Fails the login with the generic error message.
        """

        self.__fail(self.tr("Nexus Mods login failed. Close this window and try again."))

    def __fail(self, message: str) -> None:
        """
        Keeps failures from being accepted and closes the browser through its pipe.

        Args:
            message (str): Message to display instead of the login status.
        """

        if self.__cancel_event.is_set():
            return

        self.__status_label.setText(message)
        self.__stop_login()

    def __stop_login(self) -> None:
        """
        Cancels SSO, discards pending authorization data and closes the helper's input.
        """

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

        self.__stop_login()
        if not self.__browser.waitForFinished(
            NexusLoginDialog.__HELPER_SHUTDOWN_TIMEOUT
        ):
            self.__browser.kill()
            self.__browser.waitForFinished(NexusLoginDialog.__HELPER_KILL_TIMEOUT)

        super().done(result)
