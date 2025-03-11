"""
Copyright (c) Cutleast
"""

from __future__ import annotations

import urllib.parse
from pathlib import Path

from pydantic.dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class NxmRequest:
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

        scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(url)  # type: ignore

        path_parts = Path(path).parts
        game: str = netloc
        mod_id = int(path_parts[2])
        file_id = int(path_parts[4])

        parsed_query: dict[str, list[str]] = urllib.parse.parse_qs(query)

        key: str = parsed_query["key"][0]
        expires = int(parsed_query["expires"][0])
        user_id = int(parsed_query["user_id"][0])

        return NxmRequest(
            game=game,
            mod_id=mod_id,
            file_id=file_id,
            key=key,
            expires=expires,
            user_id=user_id,
        )
