"""
Copyright (c) Cutleast
"""

from __future__ import annotations

import urllib.parse

from pydantic import BaseModel


class NxmRequest(BaseModel):
    """
    Dataclass for NXM (Mod Manager Download) requests.
    """

    game: str
    """Nexus Mods game id."""

    mod_id: int
    """Nexus Mods mod id."""

    file_id: int
    """Nexus Mods file id."""

    key: str
    """Download request key."""

    expires: int
    """Download request expiration timestamp."""

    user_id: int
    """Download request user id."""

    @staticmethod
    def from_url(url: str) -> NxmRequest:
        """
        Parses an NXM Mod Manager Download URL.

        Args:
            url (str): NXM Download URL to parse.

        Returns:
            NxmRequest: Download details (mod id, file id, key, expires and user id)
        """

        parsed_url: urllib.parse.ParseResult = urllib.parse.urlparse(url)
        if parsed_url.scheme != "nxm" or not parsed_url.netloc:
            raise ValueError("The NXM request must use a game-specific nxm URL.")

        path_parts: list[str] = parsed_url.path.strip("/").split("/")
        if len(path_parts) != 4 or path_parts[0] != "mods" or path_parts[2] != "files":
            raise ValueError("The NXM request path is invalid.")

        game: str = parsed_url.netloc
        try:
            mod_id: int = int(path_parts[1])
            file_id: int = int(path_parts[3])
        except ValueError as ex:
            raise ValueError("The NXM request contains invalid identifiers.") from ex

        parsed_query: dict[str, list[str]] = urllib.parse.parse_qs(parsed_url.query)

        try:
            key: str = parsed_query["key"][0]
            expires: int = int(parsed_query["expires"][0])
            user_id: int = int(parsed_query["user_id"][0])
        except (KeyError, IndexError, ValueError) as ex:
            raise ValueError("The NXM request is missing required query parameters.") from ex

        if not key or mod_id <= 0 or file_id <= 0 or user_id <= 0:
            raise ValueError("The NXM request contains invalid values.")

        return NxmRequest(
            game=game,
            mod_id=mod_id,
            file_id=file_id,
            key=key,
            expires=expires,
            user_id=user_id,
        )
