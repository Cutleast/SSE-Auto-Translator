"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import os
import shutil
from copy import copy
from typing import Optional

import jstyleson as json
from PySide6.QtCore import QObject
from sse_bsa import BSAArchive

from app_context import AppContext
from core.archiver.archive import Archive
from core.cache.cache import Cache
from core.config.user_config import UserConfig
from core.database.string import String
from core.database.translation import Translation
from core.mod_file.mod_file import ModFile
from core.mod_file.plugin_file import PluginFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.translation_provider.source import Source
from core.utilities.constants import DSD_FILE_PATTERN
from core.utilities.container_utils import unique
from core.utilities.filesystem import parse_path, relative_data_path, safe_copy
from core.utilities.path import Path
from ui.widgets.loading_dialog import LoadingDialog


class Importer(QObject):
    """
    Class for importing translations into the database.
    """

    log: logging.Logger = logging.getLogger("Importer")

    database: "TranslationDatabase"
    user_config: UserConfig

    def __init__(
        self, database: "TranslationDatabase", user_config: UserConfig
    ) -> None:
        super().__init__()

        self.database = database
        self.user_config = user_config

    def import_mod_as_translation(self, mod: Mod, original_mod: Mod) -> None:
        """
        Imports a mod as a translation by importing all strings from
        its mod files and DSD files and creating a new translation in the database.

        Args:
            mod (Mod): The mod to import
            original_mod (Mod): The original mod
        """

        self.log.info(
            f"Importing {mod.name!r} as translation for {original_mod.name!r}."
        )

        strings: dict[str, list[String]] = {}

        # Import strings from mod files
        ignore_status: list[TranslationStatus] = [
            TranslationStatus.NoStrings,
            TranslationStatus.IsTranslated,
            TranslationStatus.TranslationInstalled,
            TranslationStatus.TranslationIncomplete,
        ]

        modfiles: dict[ModFile, ModFile] = {
            modfile: original_modfile
            for modfile in mod.modfiles
            for original_modfile in original_mod.modfiles
            if modfile.name.lower() == original_modfile.name.lower()
            and original_modfile.status not in ignore_status
        }
        """
        Map for mod files from translated mod and original mod.
        """

        self.log.debug(f"Importing strings from {len(modfiles)} mod file(s)...")
        for modfile, original_modfile in modfiles.items():
            strings[modfile.name.lower()] = self.map_translation_strings(
                modfile, original_modfile
            )

        # Import strings from DSD files
        dsd_files: list[str] = mod.dsd_files

        self.log.debug(f"Importing strings from {len(dsd_files)} DSD file(s)...")
        for dsd_file in dsd_files:
            dsd_path: Path = Path(dsd_file)

            try:
                plugin_strings: list[String] = self.extract_dsd_strings(dsd_path)

                if len(plugin_strings):
                    strings.setdefault(dsd_path.parent.name.lower(), []).extend(
                        plugin_strings
                    )
            except Exception as ex:
                self.log.error(f"Failed to import '{dsd_path}': {ex}", exc_info=ex)

        source: Source
        if mod.mod_id.mod_id and mod.mod_id.file_id:
            source = Source.NexusMods
        elif mod.mod_id.mod_id and self.user_config.language == "French":
            source = Source.Confrerie
        else:
            source = Source.Local

        translation = Translation(
            name=mod.name,
            path=self.database.userdb_path / self.database.language / mod.name,
            mod_id=mod.mod_id,
            version=mod.version,
            original_mod_id=original_mod.mod_id,
            original_version=original_mod.version,
            _strings=strings,
            source=source,
        )
        translation.save_strings()
        self.database.add_translation(translation)

        self.log.info(f"Imported translation for {len(strings)} plugin(s).")

    def extract_additional_files(
        self,
        archive_path: Path,
        original_mod: Mod,
        translation: "Translation",
        ldialog: Optional[LoadingDialog] = None,
    ) -> None:
        """
        Imports enabled additional files and that exist in the
        original mod for a translation.

        Args:
            archive_path (Path): Path to downloaded translation archive.
            original_mod (Mod): Original mod.
            translation (Translation): Installed translation.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Raises:
            ValueError: When translation path is not set
        """

        if ldialog is not None:
            ldialog.updateProgress(text1=self.tr("Processing archive..."))

        tmp_dir: Path = AppContext.get_app().get_tmp_dir()
        output_folder = tmp_dir / "Output"

        if output_folder.is_dir():
            shutil.rmtree(output_folder)

        os.mkdir(output_folder)

        archive: Archive = Archive.load_archive(archive_path)
        files_to_extract: list[str] = []
        bsa_files_to_extract: dict[Path, list[str]] = {}

        matching_files: list[str] = self.database.utils.get_additional_files(
            archive_path, ldialog
        )

        for file in matching_files:
            bsa_file, file_path = parse_path(Path(file))

            if str(file_path).lower().replace("\\", "/") in original_mod.files_names:
                if bsa_file:
                    bsa_file = tmp_dir / bsa_file.name
                    if bsa_file not in bsa_files_to_extract:
                        bsa_files_to_extract[bsa_file] = []
                    bsa_files_to_extract[bsa_file].append(str(file_path))
                else:
                    files_to_extract.append(str(file_path))
            else:
                self.log.debug(
                    f"Skipped file '{file_path}' because not in original mod files!"
                )

        if ldialog is not None:
            ldialog.updateProgress(
                text1=self.tr("Extracting files..."),
                value1=0,
                max1=0,
                show2=False,
                show3=False,
            )

        for bsa_file, files in bsa_files_to_extract.items():
            self.log.info(f"Extracting {len(files)} file(s) from '{bsa_file}'...")
            parsed_bsa = BSAArchive(bsa_file)
            for file in files:
                parsed_bsa.extract_file(file, output_folder)

        if files_to_extract:
            self.log.info(
                f"Extracting {len(files_to_extract)} file(s) from '{archive.path}'..."
            )
            archive.extract_files(files_to_extract, output_folder)
            for file in files_to_extract:
                src = output_folder / file
                dst = output_folder / relative_data_path(file)
                os.makedirs(dst.parent, exist_ok=True)
                shutil.move(src, dst, copy_function=safe_copy)  # type: ignore[arg-type]

            # Clean up
            for file in files_to_extract:
                parts = Path(file).parts
                folder = output_folder / parts[0]
                if folder.is_dir() and parts[0].lower() not in [
                    "interface",
                    "scripts",
                    "textures",
                    "sound",
                ]:
                    shutil.rmtree(folder)

        if ldialog:
            ldialog.updateProgress(text1=self.tr("Copying files..."))

        if os.listdir(output_folder):
            self.log.info(f"Moving output to '{translation.path}'...")
            shutil.move(
                output_folder,
                translation.path / "data",
                copy_function=safe_copy,  # type: ignore[arg-type]
            )
        else:
            shutil.rmtree(output_folder)
            self.log.info("Imported no additional files.")

    def extract_strings_from_archive(
        self, archive_path: Path, ldialog: Optional[LoadingDialog] = None
    ) -> dict[str, list[String]]:
        """
        Extracts strings from a downloaded archive and maps them to the
        original plugins.

        Args:
            archive_path (Path): Path to downloaded archive.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            dict[str, list[String]]: Mapping of plugin name to list of strings
        """

        translation_strings: dict[str, list[String]] = {}

        if ldialog is not None:
            ldialog.updateProgress(text1=self.tr("Processing archive..."))

        tmp_dir: Path = AppContext.get_app().get_tmp_dir()
        mod_instance: ModInstance = AppContext.get_app().mod_instance
        archive: Archive = Archive.load_archive(archive_path)

        modfiles: list[str] = []
        modfiles += archive.glob("**/*.esl")
        modfiles += archive.glob("**/*.esm")
        modfiles += archive.glob("**/*.esp")

        dsd_files: list[str] = archive.glob(DSD_FILE_PATTERN)

        self.log.debug(
            f"Extracting {len(modfiles + dsd_files)} file(s) to '{tmp_dir}'..."
        )
        archive.extract_files(modfiles + dsd_files, tmp_dir)

        self.log.debug("Processing extracted files...")

        modfile_name: str
        for m, modfile in enumerate(modfiles):
            extracted_plugin: Path = tmp_dir / modfile
            modfile_name = extracted_plugin.name

            if ldialog:
                ldialog.updateProgress(
                    text1=self.tr("Processing plugins...") + f" ({m}/{len(modfiles)})",
                    value1=m,
                    max1=len(modfiles),
                    show2=True,
                    text2=modfile_name,
                )

            # Find original plugin in modlist
            original_modfile: Optional[ModFile] = mod_instance.get_modfile(
                modfile_name,
                ignore_states=[
                    TranslationStatus.IsTranslated,
                    TranslationStatus.TranslationInstalled,
                ],
                ignore_case=True,
            )

            if original_modfile is None:
                self.log.warning(
                    f"Failed to map strings for mod file {modfile_name!r}: "
                    "Original mod file not found in modlist."
                )
                continue

            modfile_strings: list[String] = self.map_translation_strings(
                PluginFile(extracted_plugin.name, extracted_plugin), original_modfile
            )
            if modfile_strings:
                for string in modfile_strings:
                    string.status = String.Status.TranslationComplete

                translation_strings.setdefault(modfile_name.lower(), []).extend(
                    modfile_strings
                )

        for d, dsd_file in enumerate(dsd_files):
            extracted_dsd_file: Path = archive_path.parent / dsd_file
            modfile_name = extracted_dsd_file.parent.name

            if ldialog:
                ldialog.updateProgress(
                    text1=self.tr("Processing DSD files...")
                    + f" ({d}/{len(dsd_files)})",
                    value1=d,
                    max1=len(dsd_files),
                    show2=True,
                    text2=modfile_name,
                )

            strings: list[String] = self.extract_dsd_strings(extracted_dsd_file)

            if len(strings):
                translation_strings.setdefault(modfile_name.lower(), []).extend(strings)

        for modfile_name, modfile_strings in translation_strings.items():
            translation_strings[modfile_name] = unique(modfile_strings)

        self.log.info(
            f"Extracted {sum(len(strings) for strings in translation_strings.values())}"
            f" string(s) from '{archive_path}'."
        )

        return translation_strings

    def extract_dsd_strings(self, dsd_file: Path) -> list[String]:
        """
        Extracts strings from a DSD file.

        Args:
            dsd_file (Path): Path to DSD file.

        Returns:
            list[String]: List of strings
        """

        self.log.debug(f"Extracting strings from DSD file '{dsd_file}'...")

        with open(dsd_file, encoding="utf8") as file:
            string_items: list[dict[str, str]] = json.load(file)

        strings: list[String] = []
        for string_item in string_items:
            try:
                strings.append(String.from_string_data(string_item))
            except Exception as ex:
                self.log.debug(f"File: '{dsd_file}'")
                self.log.error(f"Failed to process invalid string: {ex}", exc_info=ex)

        self.log.debug(f"Extracted {len(strings)} string(s) from DSD file.")

        return strings

    def map_translation_strings(
        self, translation_modfile: ModFile, original_modfile: ModFile
    ) -> list[String]:
        """
        Extracts strings from translation and original mod files and maps them together.

        Args:
            translation_modfile (ModFile): The translated mod file
            original_modfile (ModFile): The original mod file

        Returns:
            list[String]: List of mapped strings
        """

        cache: Cache = AppContext.get_app().cache

        translation_strings: list[String] = translation_modfile.get_strings(cache)
        original_strings: list[String] = original_modfile.get_strings(cache)

        if not translation_strings and not original_strings:
            return []

        return Importer.map_strings(translation_strings, original_strings)

    @staticmethod
    def map_strings(
        translation_strings: list[String], original_strings: list[String]
    ) -> list[String]:
        """
        Maps translated strings to the original strings.

        Args:
            translation_strings (list[String]): List of translated strings
            original_strings (list[String]): List of original strings

        Returns:
            list[String]: List of mapped strings
        """

        Importer.log.debug(
            f"Mapping {len(translation_strings)} translated string(s) to "
            f"{len(original_strings)} original string(s)..."
        )

        original_strings_ids: dict[str, String] = {
            string.id: string for string in original_strings
        }

        merged_strings: list[String] = []
        unmerged_strings: list[String] = []

        for translation_string in translation_strings:
            original_string: Optional[String] = original_strings_ids.get(
                translation_string.id
            )

            if original_string is None:
                unmerged_strings.append(translation_string)
                continue

            merged_string: String = copy(translation_string)
            merged_string.translated_string = merged_string.original_string
            merged_string.original_string = original_string.original_string
            merged_string.status = String.Status.TranslationComplete
            merged_strings.append(merged_string)

        if len(unmerged_strings) < len(translation_strings):
            for unmerged_string in unmerged_strings:
                Importer.log.warning(f"Not found in Original: {unmerged_string}")

            Importer.log.debug(f"Mapped {len(merged_strings)} String(s).")
        else:
            Importer.log.error("Mapping failed!")

        return merged_strings


if __name__ == "__main__":
    from .database import TranslationDatabase
    from .translation import Translation
