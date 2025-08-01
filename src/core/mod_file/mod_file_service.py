"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject

from core.mod_instance.mod import Mod
from core.utilities.bsa_file_provider import BsaFileProvider
from core.utilities.filesystem import glob
from core.utilities.game_language import GameLanguage
from ui.widgets.loading_dialog import LoadingDialog

from .mod_file import ModFile
from .plugin_file import PluginFile

MODFILE_TYPES: list[type[ModFile]] = [
    PluginFile,
]
"""List of supported mod file types."""


class ModFileService(QObject):
    """
    Service for fetching mod files and their strings.
    """

    log: logging.Logger = logging.getLogger("ModFileService")

    def get_modfiles_from_mod(
        self,
        mod: Mod,
        language: GameLanguage,
        include_bsas: bool,
        ldialog: Optional[LoadingDialog] = None,
    ) -> list[ModFile]:
        """
        Scans the specified mod and returns all mod files.

        Args:
            mod (Mod): Mod to scan.
            language (GameLanguage): Language to filter for.
            include_bsas (bool): Whether to include mod files from BSA archives.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            list[ModFile]: List of mod files.
        """

        self.log.info(f"Scanning '{mod.name}' for mod files...")

        modfiles: list[ModFile] = []
        for file_type in MODFILE_TYPES:
            for pattern in file_type.get_glob_patterns(language.id):
                for path in map(Path, mod.glob(pattern)):
                    modfiles.append(file_type(path.name, mod.path / path))

        if include_bsas:
            for bsa_file in glob("*.bsa", mod.files):
                modfiles.extend(
                    self.get_modfiles_from_bsa(mod.path / bsa_file, language)
                )

        self.log.info(f"Found {len(modfiles)} mod files.")

        return modfiles

    def get_modfiles_from_bsa(
        self,
        bsa_file: Path,
        language: GameLanguage,
        ldialog: Optional[LoadingDialog] = None,
    ) -> list[ModFile]:
        """
        Scans the specified BSA archive and returns all mod files.

        Args:
            bsa_file (Path): Path to BSA archive.
            language (GameLanguage): Language to filter for.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            list[ModFile]: List of mod files.
        """

        self.log.info(f"Scanning '{bsa_file}' for mod files...")

        bsa_files: list[Path] = BsaFileProvider.get_file_list(bsa_file)

        modfiles: list[ModFile] = []
        for file_type in MODFILE_TYPES:
            if not file_type.can_be_in_bsas():
                continue

            for pattern in file_type.get_glob_patterns(language.id):
                for path_str in glob(pattern, bsa_files):
                    path = Path(path_str)
                    modfiles.append(file_type(path.name, bsa_file / path))

        self.log.info(f"Found {len(modfiles)} mod files.")

        return modfiles

    def get_modfiles_from_archive(
        self,
        archive_file: Path,
        language: GameLanguage,
        ldialog: Optional[LoadingDialog] = None,
    ) -> list[ModFile]:
        """
        Scans the specified archive recursively and returns all mod files.

        Args:
            archive_file (Path): Path to archive.
            language (GameLanguage): Language to filter for.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            list[ModFile]: List of mod files.
        """

        self.log.info(f"Scanning '{archive_file}' for mod files...")

        modfiles: list[ModFile] = []
        for file_type in MODFILE_TYPES:
            for pattern in file_type.get_glob_patterns(language.id):
                for path_str in BsaFileProvider.glob("**/" + pattern, archive_file):
                    path = Path(path_str)
                    modfiles.append(file_type(path.name, archive_file / path))

        self.log.info(f"Found {len(modfiles)} mod files.")

        return modfiles

    @staticmethod
    def get_modfiletype_for_suffix(suffix: str) -> type[ModFile]:
        """
        Returns a matching ModFile type for the specified file type suffix.

        Args:
            suffix (str): File type suffix

        Raises:
            NotImplementedError: when the file type is not supported

        Returns:
            type[ModFile]: ModFile type
        """

        for file_type in MODFILE_TYPES:
            if any(
                p.lower().endswith(suffix.lower())
                for p in file_type.get_glob_patterns("")
            ):
                return file_type

        raise NotImplementedError(f"File type {suffix!r} not yet supported!")
