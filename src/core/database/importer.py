"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject
from sse_bsa import BSAArchive

from core.archiver.archive import Archive
from core.config.user_config import UserConfig
from core.database.utilities import Utilities
from core.mod_file.mod_file import ModFile
from core.mod_file.mod_file_service import MODFILE_TYPES, ModFileService
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.string import StringList
from core.string.string_loader import StringLoader
from core.string.string_status import StringStatus
from core.string.string_utils import StringUtils
from core.utilities.constants import DSD_FILE_PATTERN
from core.utilities.container_utils import unique
from core.utilities.filesystem import parse_path, relative_data_path, safe_copy
from core.utilities.game_language import GameLanguage
from ui.widgets.loading_dialog import LoadingDialog


class Importer(QObject):
    """
    Class for importing translations into the database.
    """

    log: logging.Logger = logging.getLogger("Importer")

    utils = Utilities()

    @classmethod
    def import_mod_as_translation(
        cls, mod: Mod, original_mod: Mod
    ) -> dict[Path, StringList]:
        """
        Creates a translation by combining the strings from the mod files of the
        specified mods.

        Args:
            mod (Mod): The mod to use as translation.
            original_mod (Mod): The original mod.
        """

        cls.log.info(
            f"Importing '{mod.name}' as translation for '{original_mod.name}'..."
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
            for modfile in mod.modfiles
            for original_modfile in original_mod.modfiles
            if (
                (
                    modfile.path
                    == original_modfile.full_path.relative_to(original_mod.path)
                )
                and original_modfile.status not in ignore_status
            )
        }
        """
        Map for mod files from translated mod and original mod.
        """

        cls.log.debug(f"Extracting strings from {len(modfiles)} mod file(s)...")
        for modfile, original_modfile in modfiles.items():
            strings[modfile.path] = cls.map_translation_strings(
                modfile, original_modfile
            )

        # Get strings from DSD files
        dsd_files: list[str] = mod.dsd_files

        cls.log.debug(f"Extracting strings from {len(dsd_files)} DSD file(s)...")
        for dsd_file in dsd_files:
            dsd_path: Path = mod.path / dsd_file

            try:
                plugin_strings: StringList = StringLoader.load_strings_from_json_file(
                    dsd_path
                )

                if len(plugin_strings):
                    strings.setdefault(Path(dsd_path.parent), []).extend(plugin_strings)
            except Exception as ex:
                cls.log.error(f"Failed to extract from '{dsd_path}': {ex}", exc_info=ex)

        cls.log.info(
            f"Extracted {sum(len(strings) for strings in strings.values())} translated "
            f"string(s) for {len(strings)} file(s)."
        )

        return strings

    def extract_additional_files(
        self,
        archive_path: Path,
        original_mod: Mod,
        translation_path: Path,
        tmp_dir: Path,
        user_config: UserConfig,
        ldialog: Optional[LoadingDialog] = None,
    ) -> None:
        """
        Imports enabled additional files and that exist in the
        original mod for a translation.

        Args:
            archive_path (Path): Path to downloaded translation archive.
            original_mod (Mod): Original mod.
            translation_path (Path): Path to the translation's folder.
            tmp_dir (Path): Temporary directory to use.
            user_config (UserConfig): User configuration.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Raises:
            ValueError: When translation path is not set
        """

        if ldialog is not None:
            ldialog.updateProgress(text1=self.tr("Processing archive..."))

        output_folder = tmp_dir / "Output"

        if output_folder.is_dir():
            shutil.rmtree(output_folder)

        os.mkdir(output_folder)

        archive: Archive = Archive.load_archive(archive_path)
        files_to_extract: list[str] = []
        bsa_files_to_extract: dict[Path, list[str]] = {}

        matching_files: list[str] = self.utils.get_additional_files(
            archive_path, tmp_dir, user_config, ldialog
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
            self.log.info(f"Moving output to '{translation_path}'...")
            shutil.move(
                output_folder,
                translation_path / "data",
                copy_function=safe_copy,  # type: ignore[arg-type]
            )
        else:
            shutil.rmtree(output_folder)
            self.log.info("Imported no additional files.")

    def extract_strings_from_archive(
        self,
        archive_path: Path,
        mod_instance: ModInstance,
        tmp_dir: Path,
        language: GameLanguage,
        ldialog: Optional[LoadingDialog] = None,
    ) -> dict[Path, StringList]:
        """
        Extracts strings from a downloaded archive and maps them to the
        original plugins.

        Args:
            archive_path (Path): Path to downloaded archive.
            mod_instance (ModInstance): Modinstance to use.
            tmp_dir (Path): Path to the temporary directory to use.
            language (GameLanguage): Language to extract strings for.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            dict[Path, StringList]: Mapping of plugin name to list of strings
        """

        translation_strings: dict[Path, StringList] = {}

        if ldialog is not None:
            ldialog.updateProgress(text1=self.tr("Processing archive..."))

        archive: Archive = Archive.load_archive(archive_path)

        modfiles: list[str] = []

        for modfile_type in MODFILE_TYPES:
            for pattern in modfile_type.get_glob_patterns(language.id):
                modfiles.extend(archive.glob("**/" + pattern))

        dsd_files: list[str] = archive.glob("**/" + DSD_FILE_PATTERN)

        self.log.debug(
            f"Extracting {len(modfiles + dsd_files)} file(s) to '{tmp_dir}'..."
        )
        archive.extract_files(modfiles + dsd_files, tmp_dir)

        self.log.debug("Processing extracted files...")

        for m, modfile_name in enumerate(modfiles):
            extracted_file: Path = tmp_dir / modfile_name
            modfile: ModFile = ModFileService.get_modfiletype_for_suffix(
                extracted_file.suffix
            )(name=extracted_file.name, full_path=extracted_file)

            if ldialog:
                ldialog.updateProgress(
                    text1=self.tr("Processing mod files...")
                    + f" ({m}/{len(modfiles)})",
                    value1=m,
                    max1=len(modfiles),
                    show2=True,
                    text2=str(modfile.path),
                )

            # Find original plugin in modlist
            original_modfile: Optional[ModFile] = mod_instance.get_modfile(
                modfile.path,
                ignore_states=[
                    TranslationStatus.IsTranslated,
                    TranslationStatus.TranslationInstalled,
                ],
            )

            if original_modfile is None:
                self.log.warning(
                    f"Failed to map strings for mod file '{modfile.path}': "
                    "Original mod file not found in modlist."
                )
                continue

            modfile_strings: StringList = self.map_translation_strings(
                modfile, original_modfile
            )
            if modfile_strings:
                for string in modfile_strings:
                    string.status = StringStatus.TranslationComplete

                translation_strings.setdefault(modfile.path, []).extend(modfile_strings)

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

            strings: StringList = StringLoader.load_strings_from_json_file(
                extracted_dsd_file
            )

            if len(strings):
                translation_strings.setdefault(Path(modfile_name), []).extend(strings)

        for modfile_path, modfile_strings in translation_strings.items():
            translation_strings[modfile_path] = unique(modfile_strings)

        self.log.info(
            f"Extracted {sum(len(strings) for strings in translation_strings.values())}"
            f" string(s) from '{archive_path}'."
        )

        return translation_strings

    @classmethod
    def map_translation_strings(
        cls, translation_modfile: ModFile, original_modfile: ModFile
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
