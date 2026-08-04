"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path
from typing import Optional

from cutleast_core_lib.core.filesystem.utils import glob
from cutleast_core_lib.core.multithreading.progress import (
    ProgressUpdate,
    UpdateCallback,
    update,
)
from mod_manager_lib.core.instance.mod import Mod
from PySide6.QtCore import QObject

from core.file_types.file_type import FileType
from core.utilities.bsa_file_provider import BsaFileProvider
from core.utilities.game_language import GameLanguage

from .mod_file import ModFile


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
        update_callback: Optional[UpdateCallback] = None,
    ) -> list[ModFile]:
        """
        Scans the specified mod and returns all mod files.

        Args:
            mod (Mod): Mod to scan.
            language (GameLanguage): Language to filter for.
            include_bsas (bool): Whether to include mod files from BSA archives.
            update_callback (Optional[UpdateCallback], optional):
                Optional update callback. Defaults to None.

        Returns:
            list[ModFile]: List of mod files.
        """

        self.log.debug(f"Scanning '{mod.display_name}' for mod files...")

        update(
            update_callback,
            ProgressUpdate(
                status_text=self.tr("Scanning for mod files in '{modname}'...").format(
                    modname=mod.display_name
                ),
            ),
        )

        modfiles: list[ModFile] = []
        for file_type in FileType:
            file_type_cls: type[ModFile] = file_type.get_file_type_cls()
            for pattern in file_type_cls.get_glob_patterns(language.id):
                for path in mod.path.glob(pattern):
                    if path.is_file():
                        modfiles.append(file_type_cls(name=path.name, full_path=path))

        if include_bsas:
            update(
                update_callback,
                ProgressUpdate(
                    status_text=self.tr("Scanning BSAs in '{modname}'...").format(
                        modname=mod.display_name
                    ),
                ),
            )

            for bsa_file in mod.path.glob("*.bsa"):
                modfiles.extend(self.get_modfiles_from_bsa(bsa_file, language))

        self.log.debug(f"Found {len(modfiles)} mod file(s) in '{mod.display_name}'.")

        return modfiles

    def get_modfiles_from_bsa(
        self, bsa_file: Path, language: GameLanguage
    ) -> list[ModFile]:
        """
        Scans the specified BSA archive and returns all mod files.

        Args:
            bsa_file (Path): Path to BSA archive.
            language (GameLanguage): Language to filter for.

        Returns:
            list[ModFile]: List of mod files.
        """

        self.log.debug(f"Scanning '{bsa_file}' for mod files...")

        bsa_files: list[Path] = BsaFileProvider.get_cached_file_list(bsa_file)

        modfiles: list[ModFile] = []
        for file_type in FileType:
            file_type_cls: type[ModFile] = file_type.get_file_type_cls()

            if not file_type_cls.can_be_in_bsas():
                continue

            for pattern in file_type_cls.get_glob_patterns(language.id):
                for path_str in glob(pattern, bsa_files):
                    path = Path(path_str)
                    modfiles.append(
                        file_type_cls(name=path.name, full_path=bsa_file / path)
                    )

        self.log.debug(f"Found {len(modfiles)} mod files.")

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

        for file_type in FileType:
            file_type_cls: type[ModFile] = file_type.get_file_type_cls()

            if any(
                p.lower().endswith(suffix.lower())
                for p in file_type_cls.get_glob_patterns("")
            ):
                return file_type_cls

        raise NotImplementedError(f"File type '{suffix}' not yet supported!")
