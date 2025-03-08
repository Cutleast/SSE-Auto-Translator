"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from dataclasses import dataclass
from fnmatch import fnmatch
from typing import Optional, override

from sse_bsa import BSAArchive
from virtual_glob import InMemoryPath, glob

from core.utilities.constants import DSD_FILE_PATTERN
from core.utilities.path import Path

from .plugin import Plugin


@dataclass
class Mod:
    """
    Class for mods, their plugins and their metadata.
    """

    name: str
    """
    Display name of the mod.
    """

    path: Path
    """
    Path to the mod's folder.
    """

    plugins: list[Plugin]
    """
    List of plugins in mod.
    """

    mod_id: int
    file_id: int
    version: str

    __files: Optional[list[str]] = None  # type: ignore

    @property
    def files(self) -> list[str]:
        """
        List of files, including from BSAs but no BSA itself.
        """

        if self.__files is None:
            bsas = self.path.glob("*.bsa")
            files = [
                str(file.relative_to(self.path))
                for file in self.path.rglob("*")
                if not file.suffix.lower() == ".bsa" and file.is_file()
            ]

            for bsa_path in bsas:
                archive = BSAArchive(bsa_path)
                files.extend(archive.files)

            # Make case-insensitive
            for f, file in enumerate(files):
                files[f] = file.lower().replace("\\", "/")

            self.__files = files

        return self.__files

    @property
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

    def glob(self, pattern: str) -> list[str]:
        """
        Returns a list of file paths that
        match the <pattern>.

        Parameters:
            pattern: str, everything that fnmatch supports

        Returns:
            list of matching filenames
        """

        fs = InMemoryPath.from_list(self.files)
        matches = [p.path for p in glob(fs, pattern)]

        return matches

    @override
    def __hash__(self) -> int:
        return hash((self.name, self.path, self.mod_id))
