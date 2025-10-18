"""
Copyright (c) Cutleast
"""

import logging
import os
from pathlib import Path
from typing import Optional

from cutleast_core_lib.core.utilities.filesystem import add_suffix

from core.string import String, StringList, StringListModel
from core.string.string_loader import StringLoader
from core.string.string_status import StringStatus


class TranslationService:
    """
    Class for loading and saving translations.
    """

    log: logging.Logger = logging.getLogger("TranslationService")

    @classmethod
    def load_translation_strings(
        cls, translation_folder: Path
    ) -> dict[Path, StringList]:
        """
        Loads the strings for a translation from the specified folder.

        Args:
            translation_folder (Path): Path to the folder with the translation's files.

        Returns:
            dict[Path, StringList]: Map of mod file names to their list of strings.
        """

        # pre-process legacy files
        legacy_files: list[Path] = list(translation_folder.glob("*.ats"))
        for legacy_file in legacy_files:
            try:
                cls.process_legacy_file(legacy_file)
            except Exception as ex:
                cls.log.error(
                    f"Failed to process legacy file '{legacy_file}': {ex}", exc_info=ex
                )

        # then load the entire translation at once
        json_files: list[Path] = list(translation_folder.rglob("*.json"))
        strings: dict[Path, StringList] = {}
        for json_file in json_files:
            modfile_path = json_file.with_name(json_file.stem).relative_to(
                translation_folder
            )
            try:
                strings[modfile_path] = StringLoader.load_strings_from_json_file(
                    json_file
                )
            except Exception as ex:
                cls.log.error(
                    f"Failed to load strings from file '{json_file}': {ex}", exc_info=ex
                )

        return strings

    @classmethod
    def process_legacy_file(cls, legacy_ats_file_path: Path) -> StringList:
        """
        Processes a legacy .ats file by loading and converting its strings, deleting the
        original .ats file and resaving the strings to a new .json file.

        Args:
            legacy_ats_file_path (Path): Path to the legacy .ats file.

        Returns:
            StringList: List of strings.
        """

        strings: StringList = StringLoader.load_strings_from_legacy_file(
            legacy_ats_file_path
        )
        cls.save_strings_to_json_file(
            legacy_ats_file_path.with_suffix(".json"), strings
        )
        os.unlink(legacy_ats_file_path)

        return strings

    @classmethod
    def save_translation_strings(
        cls, translation_folder: Path, strings: dict[Path, StringList]
    ) -> None:
        """
        Saves the strings for a translation to the specified folder.

        Args:
            translation_folder (Path): Path to the folder to save the strings to.
            strings (dict[Path, StringList]): Map of mod file names to their list of strings.
        """

        for modfile_name, modfile_strings in strings.items():
            json_file_path: Path = translation_folder / add_suffix(
                modfile_name, ".json"
            )
            json_file_path.parent.mkdir(parents=True, exist_ok=True)
            cls.save_strings_to_json_file(json_file_path, modfile_strings)

    @classmethod
    def save_strings_to_json_file(
        cls, json_file_path: Path, strings: StringList, indent: Optional[int] = None
    ) -> None:
        """
        Saves strings to a JSON file.

        Args:
            json_file_path (Path): Path to the JSON file.
            strings (StringList): List of strings.
            indent (Optional[int], optional): Indentation level. Defaults to None.
        """

        json_file_path.write_bytes(StringListModel.dump_json(strings, indent=indent))

    @classmethod
    def update_strings(
        cls, strings_to_update: StringList, existing_strings: StringList
    ) -> None:
        """
        Updates a list of strings and attempts to translate them via similarities to
        existing strings.

        Args:
            strings_to_update (StringList): Strings to update.
            existing_strings (StringList): Existing strings to use for translation.
        """

        cls.log.info(
            f"Attempting to translate {len(strings_to_update)} string(s) from "
            f"{len(existing_strings)} existing string(s)..."
        )

        existing_strings_by_id: dict[str, String] = {
            string.id: string for string in existing_strings
        }
        existing_strings_by_original: dict[str, String] = {
            string.original: string for string in existing_strings
        }

        matched: int = 0
        for string in strings_to_update:
            matched += cls.update_string(
                string, existing_strings_by_id, existing_strings_by_original
            )

        cls.log.info(f"Successfully translated {matched} string(s).")

    @classmethod
    def update_string(
        cls,
        string_to_update: String,
        existing_strings_by_id: dict[str, String],
        existing_strings_by_original: dict[str, String],
    ) -> bool:
        """
        Updates a string and attempts to translate it via similarities to existing strings.

        Args:
            string_to_update (String): String to update.
            existing_strings_by_id (dict[str, String]): Dictionary mapping string IDs to existing strings.
            existing_strings_by_original (dict[str, String]): Dictionary mapping original strings to existing strings.

        Returns:
            bool: `True` if the string was updated, `False` otherwise.
        """

        matched: bool = False

        if string_to_update.id in existing_strings_by_id:
            existing_string = existing_strings_by_id[string_to_update.id]
            string_to_update.string = existing_string.string
            string_to_update.status = StringStatus.TranslationComplete
            matched = True

        elif string_to_update.original in existing_strings_by_original:
            existing_string = existing_strings_by_original[string_to_update.original]
            string_to_update.string = existing_string.string
            string_to_update.status = StringStatus.TranslationIncomplete
            matched = True

        return matched
