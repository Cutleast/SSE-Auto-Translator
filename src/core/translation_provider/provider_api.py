"""
Copyright (c) Cutleast
"""

import logging
import platform
from abc import abstractmethod
from pathlib import Path
from typing import NoReturn, Optional

import requests as req
from cutleast_core_lib.core.cache.cache import Cache
from PySide6.QtCore import QObject

from core.utilities.web_utils import get_url_identifier

from .exceptions import (
    ApiExpiredError,
    ApiKeyInvalidError,
    ApiLimitReachedError,
    ApiPermissionError,
    ModNotFoundError,
    Non200HttpError,
)
from .mod_details import ModDetails
from .mod_id import ModId
from .source import Source


class ProviderApi(QObject):
    """
    Base class for translation provider APIs.
    """

    log: logging.Logger

    user_agent: str
    """Application user agent to use for API requests."""

    CACHE_FOLDER = Path("web_cache")
    """The subfolder within the cache folder to store cached web requests."""

    def __init__(self) -> None:
        from app import App

        self.log = logging.getLogger(self.__class__.__name__)

        self.user_agent = (
            f"{App.APP_NAME}/"
            f"{App.APP_VERSION} "
            f"({platform.system()} {platform.version()}; "
            f"{platform.architecture()[0]})"
        )

    @Cache.persistent_cache(
        cache_subfolder=CACHE_FOLDER,
        id_generator=lambda self, url, *_: get_url_identifier(url),
        max_age=60 * 60 * 72,
    )
    def _cached_request(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        handle_status_code: bool = True,
    ) -> req.Response:
        """
        Like `_request` but uses a persistent cache with a maximum age of 72 hours.

        Args:
            url (str): URL to request
            headers (Optional[dict[str, str]], optional):
                Additional headers to send. Defaults to None.
            handle_status_code (bool, optional):
                Whether to handle the response status code and raise an Exception in case
                of a non-200 status code. Defaults to True.

        Raises:
            RequestError:
                when the request returned a non-200 HTTP status code
                and the `handle_status_code` parameter is `True`

        Returns:
            req.Response: The response
        """

        return self._request(url, headers, handle_status_code)

    def _request(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        handle_status_code: bool = True,
    ) -> req.Response:
        """
        Sends an web request to a specified url and returns the response.
        Attaches the specified headers or a default one with the application's
        user agent.

        Args:
            url (str): URL to request
            headers (Optional[dict[str, str]], optional):
                Additional headers to send. Defaults to None.
            handle_status_code (bool, optional):
                Whether to handle the response status code and raise an Exception in case
                of a non-200 status code. Defaults to True.

        Raises:
            RequestError:
                when the request returned a non-200 HTTP status code
                and the `handle_status_code` parameter is `True`

        Returns:
            req.Response: The response
        """

        if headers is None:
            headers = {"User-Agent": self.user_agent}

        self.log.debug(f"Sending API request to {url!r}...")
        res: req.Response = req.get(url, headers=headers)

        if handle_status_code:
            self.handle_status_code(url, res.status_code)

        return res

    @abstractmethod
    def is_api_key_valid(self, key: str) -> bool:
        """
        Checks if the specified key is a valid API key for this provider's API.

        Args:
            key (str): The API key to check

        Returns:
            bool: Whether the key is valid
        """

    @abstractmethod
    def is_direct_download_possible(self) -> bool:
        """
        Checks if direct downloads are possible from this provider.

        Returns:
            bool: Whether direct downloads are possible
        """

    @abstractmethod
    def get_remaining_requests(self) -> tuple[int, int]:
        """
        Returns remaining API requests for this provider.

        Returns `(-1, -1)` if there is no limit.

        Returns:
            tuple[int, int]: Remaining API requests, hourly and daily
        """

    @abstractmethod
    def get_mod_details(self, mod_id: ModId) -> ModDetails:
        """
        Requests details for the specified mod from this provider's API.

        Args:
            mod_id (ModId): Mod identifier

        Raises:
            ModNotFoundError: when the requested mod could not be found
            ProviderError: when an error occurs while requesting mod details
            UnexpectedResponseError: when the API returned an unexpected response

        Returns:
            ModDetails: Mod details
        """

    @abstractmethod
    def get_modpage_url(self, mod_id: ModId) -> str:
        """
        Gets modpage url for the specified mod.

        Args:
            mod_id (ModId): Mod identifier

        Raises:
            ModNotFoundError: when the requested mod could not be found

        Returns:
            str: Modpage url or None if not found
        """

    @abstractmethod
    def get_translations(
        self, mod_id: ModId, file_name: str, language: str
    ) -> list[ModId]:
        """
        Gets available translations for the specified file from the provider's API.

        Args:
            mod_id (ModId): Mod identifier
            file_name (str): Name of file that requires a translation.
            language (str): Language to filter for

        Returns:
            list[ModId]: List of mod file identifiers
        """

    @abstractmethod
    def is_update_available(self, mod_id: ModId, timestamp: int) -> bool:
        """
        Checks if an update is available for the specified mod and file by comparing
        the timestamps.

        Args:
            mod_id (ModId): Mod identifier
            timestamp (int): Timestamp of local file

        Raises:
            ModNotFoundError: when the requested mod could not be found

        Returns:
            bool: Whether an update is available
        """

    @abstractmethod
    def request_download(self, mod_id: ModId) -> str:
        """
        Requests a download for a mod file.

        Args:
            mod_id (ModId): Mod identifier

        Raises:
            ModNotFoundError: when the requested mod could not be found

        Returns:
            str: Download url
        """

    @classmethod
    @abstractmethod
    def get_source(cls) -> Source:
        """
        Gets the source of the provider.

        Returns:
            Source: The source
        """

    def handle_status_code(self, request_url: str, status_code: int) -> None:
        """
        Handles the status code returned by a request.

        Args:
            request_url (str): URL of the request
            status_code (int): Returned status code

        Raises:
            ApiKeyInvalidError: for status code 400
            ApiPermissionError: for status code 403
            FileNotFoundError: for status code 404
            ApiExpiredError: for status code 410
            ApiLimitReachedError: for status code 429
            Non200HttpError: for any other non-200 status code

        Returns:
            None: Returns None for status code 200
        """

        match status_code:
            case 200:
                return
            case 400:
                raise ApiKeyInvalidError(request_url)
            case 403:
                raise ApiPermissionError(request_url)
            case 404:
                raise FileNotFoundError(request_url)
            case 410:
                raise ApiExpiredError(request_url)
            case 429:
                raise ApiLimitReachedError(request_url)
            case _:
                raise Non200HttpError(request_url, status_code)

    @staticmethod
    def raise_mod_not_found_error(
        mod_id: ModId, mod_name: Optional[str] = None
    ) -> NoReturn:
        """
        Raises a ModNotFoundError with the specified mod name and ids.

        Args:
            mod_id (ModId): Mod identifier
            mod_name (Optional[str], optional): Display name of the mod, if available.
            file_id (Optional[int], optional):
                Provider-specific file id, if any. Defaults to None.

        Raises:
            ModNotFoundError: always
        """

        mod: str = str(mod_id.mod_id)
        if mod_name is not None and mod_id.file_id is None:
            mod = f"{mod_name} ({mod})"
        elif mod_name is not None and mod_id.file_id is not None:
            mod = f"{mod_name} ({mod} > {mod_id.file_id})"
        elif mod_id.file_id is not None:
            mod += f" > {mod_id.file_id}"

        raise ModNotFoundError(mod)
