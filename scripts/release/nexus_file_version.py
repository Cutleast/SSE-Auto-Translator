"""
Copyright (c) Cutleast
"""

from typing import Any, Self

from pydantic import BaseModel

from .release_error import ReleaseError


class NexusFileVersion(BaseModel, frozen=True):
    """
    A version of a Nexus Mods mod file as returned by the v3 API.
    """

    id: str
    """The API identifier of the version, returned by the upload action."""

    game_scoped_id: str
    """The public file ID, used in `?tab=files&file_id=...` download links."""

    version: str
    """The version string of this file version."""

    file_id: str
    """The API identifier of the mod file this version belongs to."""

    @classmethod
    def from_api(cls, data: Any) -> Self:
        """
        Creates a file version from a v3 `ModFileVersion` object.

        Args:
            data (Any): The decoded `ModFileVersion` JSON object.

        Raises:
            ReleaseError: The object does not contain the expected fields.

        Returns:
            Self: The file version.
        """

        if not isinstance(data, dict):
            raise ReleaseError("Nexus Mods returned an invalid file version.")

        try:
            return cls(
                id=str(data["id"]),
                game_scoped_id=str(data["game_scoped_id"]),
                version=str(data["version"]),
                file_id=str(data["file"]["id"]),
            )
        except (KeyError, TypeError) as ex:
            raise ReleaseError(
                f"Nexus Mods file version is missing the field {ex}."
            ) from ex
