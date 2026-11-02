"""
Copyright (c) Cutleast
"""

import json
from pathlib import Path

import semantic_version as semver
from pydantic import BaseModel

from .release_error import ReleaseError


class UpdateMetadata(BaseModel, frozen=True):
    """
    Content of `update.json`, which the application's updater reads from the default
    branch.
    """

    version: str
    """The latest released version."""

    download_url: str
    """Nexus Mods download link of the release, including its public file ID."""

    file_id: str
    """The public Nexus Mods file ID of the release."""

    @staticmethod
    def download_url_for(game_domain: str, mod_id: str, file_id: str) -> str:
        """
        Builds the Nexus Mods download link of a file.

        Args:
            game_domain (str): The game domain, e.g. `skyrimspecialedition`.
            mod_id (str): The public mod ID.
            file_id (str): The public file ID.

        Returns:
            str: The download link.
        """

        return (
            f"https://www.nexusmods.com/{game_domain}/mods/{mod_id}"
            f"?tab=files&file_id={file_id}"
        )

    def write(self, update_file: Path) -> bool:
        """
        Writes the metadata unless the file already announces a newer version.

        Args:
            update_file (Path): Path to `update.json`.

        Raises:
            ReleaseError: The existing file contains an invalid version.

        Returns:
            bool: Whether the file was written.
        """

        if update_file.is_file():
            current: object = json.loads(update_file.read_text(encoding="utf8"))
            current_version: object = (
                current.get("version") if isinstance(current, dict) else None
            )
            try:
                if isinstance(current_version, str) and semver.Version(
                    current_version
                ) > semver.Version(self.version):
                    return False
            except ValueError as ex:
                raise ReleaseError(
                    f"'{update_file}' contains an invalid version: {current_version}"
                ) from ex

        update_file.write_text(
            self.model_dump_json(indent=4) + "\n", encoding="utf8", newline="\n"
        )
        return True
