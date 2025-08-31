"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path
from typing import Optional

from cutleast_core_lib.core.archive.archive import Archive
from cutleast_core_lib.ui.widgets.loading_dialog import LoadingDialog
from PySide6.QtCore import QObject
from sse_bsa import BSAArchive

from core.config.user_config import UserConfig


class Utilities(QObject):
    """
    Class for import/export utility methods.
    """

    log: logging.Logger = logging.getLogger("Database.Utilities")

    def get_additional_files(
        self,
        path: Path,
        tmp_dir: Path,
        user_config: UserConfig,
        ldialog: Optional[LoadingDialog] = None,
    ) -> list[str]:
        """
        Returns a list of matching additional files from a specified path.
        The specified path should be a folder or an archive file (.7z, .rar, .zip)!
        Extracts BSAs to the temp folder if the specified path is an archive file.

        Args:
            path (Path): Path to downloaded translation archive or folder.
            tmp_dir (Path): Path to temporary directory.
            user_config (UserConfig): User configuration.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            list[str]: List of matching additional files
        """

        matching_files: list[str] = []

        lang: str = user_config.language.id
        PATTERNS: dict[str, bool] = {
            f"**/interface/**/*_{lang}.txt": user_config.enable_interface_files,
            "**/scripts/*.pex": user_config.enable_scripts,
            "**/textures/**/*.dds": user_config.enable_textures,
            "**/textures/**/*.png": user_config.enable_textures,
            "**/sound/**/*.fuz": user_config.enable_sound_files,
            "**/sound/**/*.wav": user_config.enable_sound_files,
            "**/sound/**/*.lip": user_config.enable_sound_files,
        }

        if not any(PATTERNS.values()):
            return matching_files

        if path.is_dir():
            bsa_files = [file for file in path.glob("*.bsa") if file.is_file()]

            for b, bsa_file in enumerate(bsa_files):
                if ldialog is not None:
                    ldialog.updateProgress(
                        text1=self.tr("Processing BSAs...")
                        + f" ({b}/{len(bsa_files)})",
                        value1=b,
                        max1=len(bsa_files),
                        show2=True,
                        text2=bsa_file.name,
                        value2=0,
                        max2=0,
                        show3=False,
                    )

                self.log.debug(f"Scanning '{bsa_file}'...")
                matching_files.extend(
                    Utilities.get_additional_files_from_bsa(PATTERNS, bsa_file)
                )

            for pattern, enabled in PATTERNS.items():
                if enabled:
                    matching_files.extend(
                        str(file.relative_to(path))
                        for file in path.glob(pattern)
                        if file.is_file()
                    )

        elif path.suffix.lower() in [".7z", ".rar", ".zip"]:
            if ldialog is not None:
                ldialog.updateProgress(
                    text1=self.tr("Extracting files from BSA..."),
                    value1=0,
                    max1=0,
                    show2=False,
                    show3=False,
                )

            archive = Archive.load_archive(path)
            bsas: list[str] = archive.glob("*.bsa")

            self.log.debug(f"Extracting {len(bsas)} BSA(s) from '{path}'...")
            archive.extract_files(
                [bsa for bsa in bsas if not (tmp_dir / bsa).is_file()],
                tmp_dir,
                full_paths=False,
            )

            for b, bsa in enumerate(bsas):
                bsa_file = tmp_dir / Path(bsa).name
                if ldialog:
                    ldialog.updateProgress(
                        text1=self.tr("Processing BSAs...") + f" ({b}/{len(bsas)})",
                        value1=b,
                        max1=len(bsas),
                        show2=True,
                        text2=bsa,
                        value2=0,
                        max2=0,
                        show3=False,
                    )

                self.log.debug(f"Scanning '{bsa_file}'...")
                matching_files.extend(
                    Utilities.get_additional_files_from_bsa(PATTERNS, bsa_file)
                )

            for pattern, enabled in PATTERNS.items():
                if enabled:
                    matching_files.extend(archive.glob(pattern))

        return matching_files

    @staticmethod
    def get_additional_files_from_bsa(
        patterns: dict[str, bool], bsa_file: Path
    ) -> list[str]:
        """
        Returns a list of matching additional files from a BSA archive.

        Args:
            patterns (dict[str, bool]): List of glob patterns and whether they are enabled.
            bsa_file (Path): Path to BSA archive.

        Returns:
            list[str]: List of matching additional files
        """

        matching_files: list[str] = []
        relative_bsa = Path(bsa_file.name)
        parsed_bsa = BSAArchive(bsa_file)

        for pattern, enabled in patterns.items():
            if enabled:
                matching_files.extend(
                    str(relative_bsa / file) for file in parsed_bsa.glob(pattern)
                )

        return matching_files
