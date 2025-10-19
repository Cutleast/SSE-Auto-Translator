"""
Copyright (c) Cutleast
"""

import logging
from concurrent.futures import Future, as_completed
from pathlib import Path
from typing import Optional, TypeAlias

from cutleast_core_lib.core.archive.archive import Archive
from cutleast_core_lib.core.utilities.filesystem import get_file_identifier
from cutleast_core_lib.core.utilities.progress_executor import (
    ProgressExecutor,
)
from cutleast_core_lib.ui.widgets.progress_dialog import (
    ProgressDialog,
    UpdateCallback,
    update,
)
from PySide6.QtCore import QObject

from core.file_source.archive_file_source import ArchiveFileSource
from core.mod_file.mod_file import ModFile
from core.mod_file.mod_file_service import MODFILE_TYPES, ModFileService
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.utilities.constants import DSD_FILE_PATTERN
from core.utilities.filesystem import relative_data_path
from core.utilities.game_language import GameLanguage
from core.utilities.temp_folder_provider import TempFolderProvider

from . import StringList
from .string_loader import StringLoader
from .string_utils import StringUtils

Source: TypeAlias = Path | Archive


class StringExtractor(QObject):
    """
    Class for extracting strings and mapping them to their mod file paths from archive
    files or folders.
    """

    log: logging.Logger = logging.getLogger("StringExtractor")

    def extract_strings(
        self,
        input: Path,
        mod_instance: ModInstance,
        language: GameLanguage,
        include_dsd_files: bool = True,
        pdialog: Optional[ProgressDialog] = None,
    ) -> dict[Path, StringList]:
        """
        Extracts strings from all supported mod files in an archive or directory and maps
        them to the strings of the original mod files. Mod files that have no original
        mod file installed in the mod list are ignored.

        Args:
            input (Path): Path to the archive or folder.
            mod_instance (ModInstance): Modinstance with original mod files.
            language (GameLanguage): Language to extract strings for.
            include_dsd_files (bool, optional):
                Whether to include DSD files. Defaults to True.
            pdialog (Optional[ProgressDialog], optional):
                Optional progress dialog. Defaults to None.

        Returns:
            dict[Path, StringList]: Mapping of mod file path to list of strings.
        """

        source: Source
        if input.is_file():
            source = Archive.load_archive(input)
        else:
            source = input

        self.log.info(f"Extracting strings from supported mod files in '{input}'...")
        self.log.info(f"Source is archive: {isinstance(source, Archive)}")

        if pdialog is not None:
            pdialog.updateMainProgress(
                ProgressDialog.UpdatePayload(
                    status_text=self.tr("Extracting strings from '{0}'...").format(
                        input
                    ),
                    progress_max=0,
                )
            )

        modfiles: list[Path] = self.scan_for_mod_files(source, language)

        original_modfiles: dict[ModFile, ModFile] = {}
        for modfile_path in modfiles.copy():
            modfile_data_path = Path(relative_data_path(str(modfile_path)))
            # Find original mod file in modlist
            original_modfile: Optional[ModFile] = mod_instance.get_modfile(
                modfile_data_path,
                ignore_states=[
                    TranslationStatus.IsTranslated,
                    TranslationStatus.TranslationInstalled,
                ],
            )

            if original_modfile is None:
                self.log.debug(
                    f"Skipping '{modfile_data_path}' because it has no original mod file."
                )
                modfiles.remove(modfile_path)
                continue

            modfile: ModFile = ModFileService.get_modfiletype_for_suffix(
                modfile_path.suffix
            )(name=modfile_path.name, full_path=input / modfile_path)
            original_modfiles[modfile] = original_modfile

        self.prepare_mod_files(list(original_modfiles.keys()))

        result: dict[Path, StringList] = {}

        with ProgressExecutor(pdialog) as executor:
            executor.set_main_progress_text(
                self.tr("Extracting strings from '{0}'...").format(input)
            )

            tasks: dict[Future[StringList], Path] = {}
            for modfile, original_modfile in original_modfiles.items():
                future: Future[StringList] = executor.submit(
                    # necessary as this lambda gets an update callable as first
                    # positional argument
                    lambda ucb, mf=modfile, omf=original_modfile: self.process_mod_file(
                        mf, omf, ucb
                    ),
                    modfile,
                    original_modfile,
                )
                tasks[future] = modfile.path

            for future in as_completed(tasks):
                modfile_path: Path = tasks[future]
                try:
                    modfile_strings: StringList = future.result()
                    result[modfile_path] = modfile_strings
                except Exception as ex:
                    self.log.error(
                        f"Failed to process '{modfile_path}': {ex}", exc_info=ex
                    )

        if include_dsd_files:
            result.update(self.extract_dsd_strings(input, mod_instance))

        self.log.info(f"Successfully extracted strings from {len(result)} mod file(s).")

        return result

    def prepare_mod_files(self, modfiles: list[ModFile]) -> None:
        """
        Prepares the mod files for string extraction by extracting them from archives if
        necessary.

        Args:
            modfiles (list[ModFile]): List of mod files.
        """

        self.log.info(f"Preparing {len(modfiles)} mod file(s) for string extraction...")

        if not modfiles:
            return

        archive_path: Optional[Path] = None
        archive_path, _ = ArchiveFileSource.split_path_with_archive(
            modfiles[0].full_path
        )

        if archive_path is None:
            return

        to_extract: dict[Path, ModFile] = {}
        for file in modfiles:
            file_path: Optional[Path] = None
            _, file_path = ArchiveFileSource.split_path_with_archive(file.full_path)

            if file_path is None:
                continue

            to_extract[file_path] = file

        out_folder: Path = TempFolderProvider.get().get_temp_folder()
        out_folder /= get_file_identifier(archive_path)
        out_folder.mkdir(parents=True, exist_ok=True)

        archive: Archive = Archive.load_archive(archive_path)
        archive.extract_files(list(map(str, to_extract.keys())), out_folder)

        for file_path, modfile in to_extract.items():
            modfile.full_path = out_folder / file_path

    def process_mod_file(
        self,
        translated_modfile: ModFile,
        original_modfile: ModFile,
        update_callback: Optional[UpdateCallback] = None,
    ) -> StringList:
        """
        Processes a file by extracting its strings and mapping them to the original mod file.

        Args:
            translated_modfile (ModFile): Translated mod file.
            original_modfile (ModFile): Original mod file.
            update_callback (Optional[UpdateCallback], optional):
                Optional update callback. Defaults to None.

        Returns:
            StringList: List of mapped strings.
        """

        update(
            update_callback,
            ProgressDialog.UpdatePayload(
                status_text=self.tr("Processing '{0}'...").format(
                    translated_modfile.full_path
                ),
                progress_max=0,
            ),
        )

        modfile_strings: StringList = self.map_translation_strings(
            translated_modfile, original_modfile
        )

        return modfile_strings

    def scan_for_mod_files(self, source: Source, language: GameLanguage) -> list[Path]:
        """
        Scans a folder or archive for supported mod files and returns their paths,
        relative to the source.

        Args:
            source (Source): Path to the folder or archive.
            language (GameLanguage): Language to filter for.

        Returns:
            list[Path]: List of mod file paths.
        """

        mod_files: list[Path] = []
        for file_type in MODFILE_TYPES:
            for pattern in file_type.get_glob_patterns(language.id):
                for path in source.glob("**/" + pattern):
                    if isinstance(source, Archive):
                        # archives already return relative paths
                        mod_files.append(Path(path))
                    else:
                        # pathlib returns absolute paths
                        mod_files.append(Path(path).relative_to(source))

        self.log.info(f"Found {len(mod_files)} supported mod files.")

        return mod_files

    def extract_dsd_strings(
        self, input: Path, mod_instance: ModInstance
    ) -> dict[Path, StringList]:
        """
        Extracts strings from all Dynamic String Distributor files in an archive or
        directory.

        Args:
            input (Path): Path to the archive or directory.
            mod_instance (ModInstance): Modinstance with original mod files.

        Returns:
            dict[Path, StringList]: Mapping of mod file path to list of strings.
        """

        source: Source
        if input.is_file():
            source = Archive.load_archive(input)
        else:
            source = input

        self.log.info(f"Extracting strings from DSD files in '{input}'...")
        self.log.info(f"Source is archive: {isinstance(source, Archive)}")

        dsd_files: dict[Path, Path] = self.scan_for_dsd_files(source)
        self.prepare_dsd_files(source, dsd_files)

        result: dict[Path, StringList] = {}
        for mod_file, dsd_file in dsd_files.items():
            # Find original mod file in modlist
            original_modfile: Optional[ModFile] = mod_instance.get_modfile(
                mod_file,
                ignore_states=[
                    TranslationStatus.IsTranslated,
                    TranslationStatus.TranslationInstalled,
                ],
            )

            if original_modfile is None:
                self.log.debug(
                    f"Skipping '{mod_file}' because it has no original mod file."
                )
                continue

            result[mod_file] = StringLoader.load_strings_from_json_file(dsd_file)

        self.log.info(f"Successfully extracted strings from {len(result)} DSD file(s).")

        return result

    def scan_for_dsd_files(self, source: Source) -> dict[Path, Path]:
        """
        Scans an archive or folder for Dynamic String Distributor files.

        Args:
            source (Source): Path to the archive or folder.

        Returns:
            dict[Path, Path]:
                Mapping of mod file path to DSD file path, relative to the source.
        """

        result: dict[Path, Path] = {}

        for path in source.glob("**/" + DSD_FILE_PATTERN):
            path = Path(path)
            modfile_path = Path(path.parent.name)

            if not isinstance(source, Archive):
                path = path.relative_to(source)

            result[modfile_path] = path

        self.log.info(f"Found {len(result)} DSD files.")

        return result

    def prepare_dsd_files(self, source: Source, dsd_files: dict[Path, Path]) -> None:
        """
        Prepares the DSD files for string extraction by extracting them from archives if
        necessary.

        Args:
            source (Source): Path to the archive or folder.
            dsd_files (dict[Path, Path]): Mapping of mod file path to DSD file path.
        """

        self.log.info(
            f"Preparing {len(dsd_files)} DSD file(s) for string extraction..."
        )

        if not dsd_files:
            return

        if not isinstance(source, Archive):
            return

        out_folder: Path = TempFolderProvider.get().get_temp_folder()
        out_folder /= get_file_identifier(source.path)
        out_folder.mkdir(parents=True, exist_ok=True)

        to_extract: dict[Path, Path] = {}
        for mod_file, dsd_file in dsd_files.items():
            file_path: Optional[Path] = None
            _, file_path = ArchiveFileSource.split_path_with_archive(dsd_file)

            if file_path is None:
                continue

            to_extract[file_path] = mod_file

        source.extract_files(list(map(str, to_extract.keys())), out_folder)

        for file_path, mod_file in to_extract.items():
            dsd_files[mod_file] = out_folder / file_path

    @classmethod
    def map_strings_from_mods(
        cls, translated_mod: Mod, original_mod: Mod
    ) -> dict[Path, StringList]:
        """
        Creates a translation by combining the strings from the mod files of the
        specified mods.

        Args:
            translated_mod (Mod): The mod to use as translation.
            original_mod (Mod): The original mod.
        """

        cls.log.info(
            f"Importing '{translated_mod.name}' as translation for '{original_mod.name}'..."
        )

        strings: dict[Path, StringList] = {}

        # Get strings from mod files
        ignore_status: list[TranslationStatus] = [
            TranslationStatus.NoStrings,
            TranslationStatus.IsTranslated,
            TranslationStatus.TranslationInstalled,
            TranslationStatus.TranslationIncomplete,
        ]

        modfiles: dict[ModFile, ModFile] = {
            modfile: original_modfile
            for modfile in translated_mod.modfiles
            for original_modfile in original_mod.modfiles
            if (
                modfile.path == original_modfile.path
                and original_modfile.status not in ignore_status
            )
        }
        """
        Map for mod files from translated mod and original mod.
        """

        cls.log.debug(f"Extracting strings from {len(modfiles)} mod file(s)...")
        for modfile, original_modfile in modfiles.items():
            strings[modfile.path] = StringExtractor.map_translation_strings(
                modfile, original_modfile
            )

        # Get strings from DSD files
        dsd_files: list[Path] = translated_mod.dsd_files
        original_modfiles: list[Path] = [
            modfile.path
            for modfile in original_mod.modfiles
            if modfile.status not in ignore_status
        ]

        cls.log.debug(f"Extracting strings from {len(dsd_files)} DSD file(s)...")
        for dsd_file in dsd_files:
            dsd_path: Path = translated_mod.path / dsd_file
            mod_file = Path(dsd_path.parent.name)

            if mod_file not in original_modfiles:
                cls.log.debug(
                    f"Skipped DSD file '{dsd_file}' due to missing original mod file "
                    f"'{mod_file}'."
                )
                continue

            try:
                plugin_strings: StringList = StringLoader.load_strings_from_json_file(
                    dsd_path
                )

                if len(plugin_strings):
                    strings.setdefault(mod_file, []).extend(plugin_strings)
            except Exception as ex:
                cls.log.error(f"Failed to extract from '{dsd_path}': {ex}", exc_info=ex)

        cls.log.info(
            f"Extracted {sum(len(strings) for strings in strings.values())} translated "
            f"string(s) for {len(strings)} file(s)."
        )

        return strings

    @staticmethod
    def map_translation_strings(
        translation_modfile: ModFile, original_modfile: ModFile
    ) -> StringList:
        """
        Extracts strings from translation and original mod files and maps them together.

        Args:
            translation_modfile (ModFile): The translated mod file
            original_modfile (ModFile): The original mod file

        Returns:
            StringList: List of mapped strings
        """

        translation_strings: StringList = translation_modfile.get_strings()
        original_strings: StringList = original_modfile.get_strings()

        if not translation_strings and not original_strings:
            return []

        return StringUtils.map_strings(original_strings, translation_strings)
