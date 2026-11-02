"""
Copyright (c) Cutleast
"""

import json
import time
import urllib.error
import urllib.request
from typing import Any

from .nexus_file_version import NexusFileVersion
from .release_error import ReleaseError, RetryableReleaseError


class NexusClient:
    """
    Minimal read-only client for the Nexus Mods v3 API.

    Uploading is done by the official `Nexus-Mods/upload-action`; this client only reads
    the resulting file versions.
    """

    BASE_URL: str = "https://api.nexusmods.com/v3"
    """Base URL of the Nexus Mods v3 API."""

    USER_AGENT: str = "SSE-Auto-Translator release workflow"
    """User agent sent with every request."""

    MAX_ATTEMPTS: int = 5
    """Number of attempts for requests that fail temporarily."""

    __api_key: str

    def __init__(self, api_key: str) -> None:
        """
        Args:
            api_key (str): Nexus Mods API key; kept in memory only.

        Raises:
            ReleaseError: No API key was provided.
        """

        if not api_key:
            raise ReleaseError("NEXUSMODS_API_KEY is not configured.")

        self.__api_key = api_key

    def get_file_versions(self, file_id: str) -> list[NexusFileVersion]:
        """
        Gets all versions of a mod file.

        Args:
            file_id (str): API identifier of the mod file.

        Raises:
            ReleaseError: The request failed or returned an invalid response.

        Returns:
            list[NexusFileVersion]: The versions of the mod file.
        """

        response: dict[str, Any] = self.__get_json(f"/mod-files/{file_id}/versions")
        versions: Any = response.get("data", {}).get("versions")
        if not isinstance(versions, list):
            raise ReleaseError("Nexus Mods returned no version list for the file.")

        return [NexusFileVersion.from_api(version) for version in versions]

    def get_version(self, version_id: str) -> NexusFileVersion:
        """
        Gets a single mod file version.

        Args:
            version_id (str): API identifier of the version.

        Raises:
            ReleaseError: The request failed or returned an invalid response.

        Returns:
            NexusFileVersion: The file version.
        """

        response: dict[str, Any] = self.__get_json(f"/mod-file-versions/{version_id}")
        return NexusFileVersion.from_api(response.get("data"))

    def __get_json(self, path: str) -> dict[str, Any]:
        """
        Sends a GET request and retries temporary failures with a backoff.

        Args:
            path (str): API path relative to the base URL.

        Raises:
            ReleaseError: The request failed permanently or after all attempts.

        Returns:
            dict[str, Any]: The decoded JSON response.
        """

        last_error: RetryableReleaseError = RetryableReleaseError("No request was sent.")
        for attempt in range(NexusClient.MAX_ATTEMPTS):
            try:
                return self.__request(path)
            except RetryableReleaseError as ex:
                last_error = ex
                time.sleep(min(2**attempt * 2, 30))

        raise ReleaseError(f"{last_error} (after {NexusClient.MAX_ATTEMPTS} attempts)")

    def __request(self, path: str) -> dict[str, Any]:
        """
        Sends a single GET request.

        Args:
            path (str): API path relative to the base URL.

        Raises:
            RetryableReleaseError: Rate limiting, a server error or a network error.
            ReleaseError: Any other HTTP error or an invalid response.

        Returns:
            dict[str, Any]: The decoded JSON response.
        """

        url: str = NexusClient.BASE_URL + path
        request = urllib.request.Request(
            url,
            headers={
                "apikey": self.__api_key,
                "Accept": "application/json",
                "User-Agent": NexusClient.USER_AGENT,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                result: Any = json.load(response)
        except urllib.error.HTTPError as ex:
            detail: str = ex.read().decode("utf8", errors="replace")[:500]
            message: str = f"Nexus Mods returned HTTP {ex.code} for {url}: {detail}"
            if ex.code == 429 or ex.code >= 500:
                raise RetryableReleaseError(message) from ex
            raise ReleaseError(message) from ex
        except urllib.error.URLError as ex:
            raise RetryableReleaseError(f"Request to {url} failed: {ex.reason}") from ex

        if not isinstance(result, dict):
            raise ReleaseError(f"Nexus Mods returned an invalid response for {url}.")

        return result
