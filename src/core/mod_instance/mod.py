"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from dataclasses import dataclass
from fnmatch import fnmatch
from functools import cache
from typing import override

from sse_bsa import BSAArchive

from core.cache.cache import Cache
from core.mod_file.mod_file import ModFile
from core.translation_provider.mod_id import ModId
from core.utilities.constants import DSD_FILE_PATTERN
from core.utilities.filesystem import get_file_identifier, glob, parse_path
from core.utilities.path import Path


@dataclass
class Mod:
    """
    Class for mods, their mod files and their metadata.
    """

    name: str
    """Display name of the mod."""

    path: Path
    """Path to the mod's folder."""

    modfiles: list[ModFile]
    """List of translatable files in mod."""

    mod_id: ModId
    """Identifier of this mod at its source."""

    version: str
    """Local version of the mod."""

    @property
    @cache
    def files_names(self) -> list[str]:
        """
        List of files, including from BSAs but removing the BSA parts, relative to this
        mod's path.
        """

        return [
            str(parse_path(file)[1]).lower().replace("\\", "/") for file in self.files
        ]

    @property
    @cache
    def files(self) -> list[Path]:
        """
        List of all files in the mod, treating BSA archives as folders, relative to this
        mod's path.
        """

        files: list[Path] = [
            f.relative_to(self.path)
            for f in self.path.rglob("*")
            if not f.suffix.lower() == ".bsa" and f.is_file()
        ]

        for bsa_path in self.path.glob("*.bsa"):
            files += Mod.__get_files_from_bsa(bsa_path, self.path)

        return files

    @property
    @cache
    def dsd_files(self) -> list[str]:
        """
        List of all DSD files in the mod, excluding the ones from generated Output mod.
        """

        return [
            file
            for file in self.glob(DSD_FILE_PATTERN)
            if not fnmatch(
                file, "*_SSEAT.json"
            )  # Do not import DSD files from generated Output mod
        ]

    def glob(self, pattern: str, case_sensitive: bool = False) -> list[str]:
        """
        Returns a list of file paths that match the specified pattern.

        Args:
            pattern (str): Glob pattern.
            case_sensitive (bool, optional): Case sensitive. Defaults to False.

        Returns:
            list[str]: List of matching files, relative to this mod's path
        """

        return glob(pattern, [str(f) for f in self.files], case_sensitive)

    @staticmethod
    @Cache.persistent_cache(
        cache_subfolder=Path("mod_cache"),
        id_generator=lambda bsa_path, mod_path: get_file_identifier(bsa_path),
    )
    def __get_files_from_bsa(bsa_path: Path, mod_path: Path) -> list[Path]:
        archive = BSAArchive(bsa_path)
        return [bsa_path.relative_to(mod_path) / f for f in archive.files]

    @override
    def __hash__(self) -> int:
        return hash((self.name, self.path, self.mod_id))
