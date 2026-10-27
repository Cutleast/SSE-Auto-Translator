"""
Copyright (c) Cutleast
"""

import json
from base64 import b64decode, b64encode
from hashlib import sha256
from http.cookiejar import Cookie, CookieJar
from threading import Lock
from typing import Optional, Self

from curl_cffi import requests
from pydantic import BaseModel, SecretStr, ValidationError
from PySide6.QtNetwork import QNetworkCookie
from pywintypes import error as WindowsError
from win32crypt import CryptProtectData, CryptUnprotectData
from win32cryptcon import CRYPTPROTECT_UI_FORBIDDEN


class NexusWebSession:
    """
    Reuses the website cookies obtained during the Nexus API login.
    """

    class __StoredSession(BaseModel):
        """
        Validates decrypted session data without exposing cookie values in repr.
        """

        account: str
        """The fingerprint of the API key associated with the cookies."""

        user_agent: str
        """The user agent of the browser that obtained the cookies."""

        cookies: list[SecretStr]
        """The serialized Nexus website cookies."""

    __client: requests.Session
    __pages: dict[str, bytes]
    __lock: Lock

    def __init__(self, cookies: list[QNetworkCookie], user_agent: str) -> None:
        """
        Args:
            cookies (list[QNetworkCookie]): Website cookies from the SSO browser.
            user_agent (str): User agent used by the SSO browser.
        """

        jar = CookieJar()
        for cookie in cookies:
            domain: str = cookie.domain()
            if domain not in {".nexusmods.com", "www.nexusmods.com"}:
                continue
            jar.set_cookie(
                Cookie(
                    version=0,
                    name=bytes(cookie.name().data()).decode("latin-1"),
                    value=bytes(cookie.value().data()).decode("latin-1"),
                    port=None,
                    port_specified=False,
                    domain=domain,
                    domain_specified=domain.startswith("."),
                    domain_initial_dot=domain.startswith("."),
                    path=cookie.path() or "/",
                    path_specified=bool(cookie.path()),
                    secure=cookie.isSecure(),
                    expires=(
                        None
                        if cookie.isSessionCookie()
                        else cookie.expirationDate().toSecsSinceEpoch()
                    ),
                    discard=cookie.isSessionCookie(),
                    comment=None,
                    comment_url=None,
                    rest={"HttpOnly": ""} if cookie.isHttpOnly() else {},
                )
            )
        self.__client = requests.Session(
            impersonate="chrome", cookies=jar, headers={"User-Agent": user_agent}
        )
        self.__pages = {}
        self.__lock = Lock()

    @staticmethod
    def encrypt(cookies: list[QNetworkCookie], user_agent: str, api_key: str) -> str:
        """
        Protects website cookies for the current Windows user and API account.

        Args:
            cookies (list[QNetworkCookie]): Cookies from the SSO browser.
            user_agent (str): User agent of the SSO browser.
            api_key (str): API key issued by the same login.

        Returns:
            str: Encrypted session suitable for saving in the user configuration.

        Raises:
            WindowsError: If Windows cannot encrypt the session.
        """

        payload: dict[str, str | list[str]] = {
            "account": sha256(api_key.encode()).hexdigest(),
            "user_agent": user_agent,
            "cookies": [
                bytes(cookie.toRawForm().data()).decode("latin-1")
                for cookie in cookies
                if cookie.domain() in {".nexusmods.com", "www.nexusmods.com"}
            ],
        }
        encrypted: bytes = CryptProtectData(
            json.dumps(payload).encode(),
            "SSE-AT Nexus website session",
            None,
            None,
            None,
            CRYPTPROTECT_UI_FORBIDDEN,
        )
        return b64encode(encrypted).decode("ascii")

    @classmethod
    def restore(cls, encrypted: str, api_key: str) -> Optional[Self]:
        """
        Restores website access for the same Windows user and API account.

        Args:
            encrypted (str): Previously encrypted session.
            api_key (str): Currently configured API key.

        Returns:
            Optional[Self]: Restored session, or None if it cannot be recovered.
        """

        try:
            _, payload = CryptUnprotectData(
                b64decode(encrypted, validate=True),
                None,
                None,
                None,
                CRYPTPROTECT_UI_FORBIDDEN,
            )
            data: NexusWebSession.__StoredSession = (
                cls.__StoredSession.model_validate_json(payload)
            )
        except ValueError, WindowsError, ValidationError:
            return None
        if data.account != sha256(api_key.encode()).hexdigest():
            return None
        cookies: list[QNetworkCookie] = [
            cookie
            for raw in data.cookies
            for cookie in QNetworkCookie.parseCookies(
                raw.get_secret_value().encode("latin-1")
            )
        ]
        return cls(cookies, data.user_agent)

    def get_page(self, url: str) -> tuple[int, bytes]:
        """
        Fetches a Nexus page without persisting responses or request credentials.

        Args:
            url (str): Nexus website URL to retrieve.

        Returns:
            tuple[int, bytes]: HTTP status and response body.

        Raises:
            ValueError: If the URL does not target the Nexus website.
            requests.RequestsError: If the website request fails.
        """

        if not url.startswith("https://www.nexusmods.com/"):
            raise ValueError("Website sessions are restricted to Nexus Mods HTTPS.")
        with self.__lock:
            if url in self.__pages:
                return 200, self.__pages[url]
            response: requests.Response = self.__client.get(url, timeout=(5.0, 30.0))
            if response.status_code == 200:
                if len(self.__pages) >= 32:
                    self.__pages.pop(next(iter(self.__pages)))
                self.__pages[url] = response.content
            return response.status_code, response.content

    def is_expired(self) -> bool:
        """
        Checks whether the website authentication cookie is missing or expired.

        Returns:
            bool: Whether no usable authentication cookie remains.
        """

        with self.__lock:
            return not any(
                cookie.name == "nexusmods_session"
                and cookie.domain in {".nexusmods.com", "www.nexusmods.com"}
                and bool(cookie.value)
                and not cookie.is_expired()
                for cookie in self.__client.cookies.jar
            )
