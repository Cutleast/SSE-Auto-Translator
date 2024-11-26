"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import QTreeWidgetItem
from virtual_glob import InMemoryPath, glob

from core.archive_parser.archive_parser import ArchiveParser

from .plugin import Plugin


@dataclass
class Mod:
    """
    Class for mods, their plugins and their metadata.
    """

    name: str  # Full Mod Name
    path: Path  # Path to mod's folder
    plugins: list[Plugin]  # List of plugins in mod

    mod_id: int
    file_id: int
    version: str

    tree_item: QTreeWidgetItem = None

    __files: list[str] = None

    @property
    def files(self):
        """
        List of files, including from BSAs but no BSA itself.
        """

        if not self.__files:
            bsas = self.path.glob("*.bsa")
            files = [
                str(file.relative_to(self.path))
                for file in self.path.rglob("*")
                if not file.suffix.lower() == ".bsa"
                and file.is_file()
            ]

            for bsa_path in bsas:
                parser = ArchiveParser(bsa_path)
                files.extend(parser.parse_archive().glob("**/*.*"))

            # Make case-insensitive
            for f, file in enumerate(files):
                files[f] = file.lower().replace("\\", "/")

            self.__files = files

        return self.__files

    def glob(self, pattern: str):
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

    def __getstate__(self):
        state = self.__dict__.copy()

        # Don't pickle tree_item
        del state["tree_item"]

        # Don't pickle __files that could change
        del state["__files"]

        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

        # Add tree_item back
        self.tree_item = None

        # Add __files back
        self.__files = None
