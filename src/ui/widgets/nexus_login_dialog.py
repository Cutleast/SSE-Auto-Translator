"""
Copyright (c) Cutleast
"""

import logging
from threading import Event, Thread
from typing import ClassVar, Optional, override

from PySide6.QtCore import QDateTime, QTimer, QUrl, Signal, Slot
from PySide6.QtNetwork import QNetworkCookie
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QWidget
from pywintypes import error as WindowsError

from core.translation_provider.nm_api.nm_api import NexusModsApi
from core.translation_provider.nm_api.web_session import NexusWebSession


class NexusLoginDialog(QDialog):
    """
    Obtains the API key and website session through one embedded Nexus SSO login.
    """

    log: ClassVar[logging.Logger] = logging.getLogger("NexusLoginDialog")
    """Logs failure categories without authorization payloads or tracebacks."""

    __open_page = Signal(str)
    """Requests navigation to the SSO authorization page on the GUI thread."""

    __authorized = Signal(str)
    """Delivers the API key issued by the SSO server to the GUI thread."""

    __failed = Signal()
    """Reports an SSO failure without exposing authorization data."""

    __browser: QWebEngineView
    __profile: QWebEngineProfile
    __status_label: QLabel
    __cancel_event: Event
    __cookies: dict[tuple[str, str, bytes], QNetworkCookie]
    __thread: Thread
    __pending_api_key: Optional[str]
    __session_timeout: QTimer

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
        self.setWindowTitle(self.tr("Nexus Mods login"))
        self.resize(1100, 850)
        self.api_key = None
        self.website_session = None
        self.__pending_api_key = None
        self.__cookies = {}
        self.__cancel_event = Event()
        self.__init_ui()
        self.__session_timeout = QTimer(self)
        self.__session_timeout.setSingleShot(True)
        self.__session_timeout.setInterval(30000)
        self.__session_timeout.timeout.connect(self.__show_error)
        self.__profile.cookieStore().cookieAdded.connect(self.__on_cookie_added)
        self.__profile.cookieStore().cookieRemoved.connect(self.__on_cookie_removed)
        self.__open_page.connect(self.__navigate)
        self.__authorized.connect(self.__finish_login)
        self.__failed.connect(self.__show_error)
        self.finished.connect(lambda _: self.__cancel_event.set())
        self.__thread = Thread(target=self.__run_sso, daemon=True)
        QTimer.singleShot(0, self.__thread.start)

    def __init_ui(self) -> None:
        """
        Creates the SSO browser and cancellation control.
        """

        layout = QVBoxLayout(self)
        self.__status_label = QLabel(self.tr("Connecting to Nexus Mods..."))
        self.__status_label.setWordWrap(True)
        layout.addWidget(self.__status_label)
        self.__browser = QWebEngineView(self)
        self.__profile = QWebEngineProfile(self.__browser)
        page = QWebEnginePage(self.__profile, self.__browser)
        self.__browser.setPage(page)
        layout.addWidget(self.__browser, stretch=1)
        cancel_button = QPushButton(self.tr("Cancel"))
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)

    @Slot(str)
    def __navigate(self, url: str) -> None:
        """
        Opens the existing SSO URL in the embedded browser.

        Args:
            url (str): Authorization URL issued for this SSO attempt.
        """

        if not self.__cancel_event.is_set():
            self.__status_label.setText(
                self.tr("Sign in to Nexus Mods and authorize SSE-AT to continue.")
            )
            self.__browser.setUrl(QUrl(url))

    @Slot(QNetworkCookie)
    def __on_cookie_added(self, cookie: QNetworkCookie) -> None:
        """
        Collects cookies belonging to the Nexus website.

        Args:
            cookie (QNetworkCookie): Added or updated browser cookie.
        """

        if cookie.domain() in {".nexusmods.com", "www.nexusmods.com"}:
            key: tuple[str, str, bytes] = (
                cookie.domain(),
                cookie.path(),
                bytes(cookie.name().data()),
            )
            self.__cookies[key] = QNetworkCookie(cookie)
            if (
                self.__pending_api_key is not None
                and cookie.name() == b"nexusmods_session"
            ):
                QTimer.singleShot(0, self.__complete_login)

    @Slot(QNetworkCookie)
    def __on_cookie_removed(self, cookie: QNetworkCookie) -> None:
        """
        Drops cookies invalidated by the website.

        Args:
            cookie (QNetworkCookie): Removed browser cookie.
        """

        key: tuple[str, str, bytes] = (
            cookie.domain(),
            cookie.path(),
            bytes(cookie.name().data()),
        )
        self.__cookies.pop(key, None)

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
        Waits for the browser's authentication cookie after API authorization.

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
        self.__profile.cookieStore().loadAllCookies()
        self.__complete_login()

    @Slot()
    def __complete_login(self) -> None:
        """
        Completes SSO only after the store delivers the website authentication cookie.
        """

        key: Optional[str] = self.__pending_api_key
        if key is None or self.__cancel_event.is_set():
            return
        if not any(
            cookie.name() == b"nexusmods_session"
            and not cookie.value().isEmpty()
            and (
                cookie.isSessionCookie()
                or cookie.expirationDate() > QDateTime.currentDateTimeUtc()
            )
            for cookie in self.__cookies.values()
        ):
            return
        try:
            self.website_session = NexusWebSession.encrypt(
                list(self.__cookies.values()), self.__profile.httpUserAgent(), key
            )
        except WindowsError:
            self.__show_error()
            return
        self.api_key = key
        self.accept()

    @Slot()
    def __show_error(self) -> None:
        """
        Keeps a failed or cancelled login from being treated as successful.
        """

        self.__status_label.setText(
            self.tr("Nexus Mods login failed. Close this window and try again.")
        )
        self.__cancel_event.set()
        self.__session_timeout.stop()

    @override
    def done(self, result: int) -> None:
        """
        Stops the browser and releases its page before destroying its profile.

        Args:
            result (int): Dialog result to return to the setup widget.
        """

        self.__session_timeout.stop()
        self.__browser.stop()
        super().done(result)
        self.__browser.page().deleteLater()
        self.__profile.deleteLater()
