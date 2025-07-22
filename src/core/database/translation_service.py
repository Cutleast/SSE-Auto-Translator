"""
Copyright (c) Cutleast
"""

import logging
import os
from pathlib import Path
from types import ModuleType
from typing import Optional, TypeAlias

from pydantic import TypeAdapter

from core import plugin_interface, utilities
from core.utilities.alias_unpickler import AliasUnpickler

from . import legacy_string
from .legacy_string import LegacyString
from .string import String

StringList: TypeAlias = list[String]
StringListModel = TypeAdapter(StringList)


class TranslationService:
    """
    Class for loading and saving translations.
    """

    MODULE_ALIASES: dict[str, ModuleType] = {
        "core.database.string": legacy_string,
        "plugin_parser": plugin_interface,
        "plugin_parser.string": legacy_string,
        "utilities": utilities,
        "utilities.string": legacy_string,
        "plugin_interface": plugin_interface,
    }
    """Dict of module aliases required for deserialization of older translations."""

    CLASS_ALIASES: dict[str, str] = {
        "String": "LegacyString",
        "String.Status": "LegacyString.Status",
    }
    """Dict of class aliases required for deserialization of older translations."""

    log: logging.Logger = logging.getLogger("TranslationService")

    @classmethod
    def load_translation_strings(
        cls, translation_folder: Path
    ) -> dict[str, list[String]]:
        """
        Loads the strings for a translation from the specified folder.

        Args:
            translation_folder (Path): Path to the folder with the translation's files.

        Returns:
            dict[str, list[String]]: Map of mod file names to their list of strings.
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
        json_files: list[Path] = list(translation_folder.glob("*.json"))
        strings: dict[str, list[String]] = {}
        for json_file in json_files:
            try:
                strings[json_file.stem] = cls.load_strings_from_json_file(json_file)
            except Exception as ex:
                cls.log.error(
                    f"Failed to load strings from file '{json_file}': {ex}", exc_info=ex
                )

        return strings

    @classmethod
    def load_strings_from_json_file(cls, json_file_path: Path) -> list[String]:
        """
        Loads strings from a JSON file.

        Args:
            json_file_path (Path): Path to the JSON file.

        Returns:
            list[String]: List of strings.
        """

        return StringListModel.validate_json(json_file_path.read_bytes())

    @classmethod
    def process_legacy_file(cls, legacy_ats_file_path: Path) -> list[String]:
        """
        Processes a legacy .ats file by loading and converting its strings, deleting the
        original .ats file and resaving the strings to a new .json file.

        Args:
            legacy_ats_file_path (Path): Path to the legacy .ats file.

        Returns:
            list[String]: List of strings.
        """

        strings: list[String] = cls.load_strings_from_legacy_file(legacy_ats_file_path)
        cls.save_strings_to_json_file(
            legacy_ats_file_path.with_suffix(".json"), strings
        )
        os.unlink(legacy_ats_file_path)

        return strings

    @classmethod
    def load_strings_from_legacy_file(cls, legacy_ats_file_path: Path) -> list[String]:
        """
        Deserializes and converts strings from a legacy .ats file to the new String
        class.

        Args:
            legacy_ats_file_path (Path): Path to the legacy .ats file.

        Returns:
            list[String]: List of strings.
        """

        strings: list[LegacyString] = AliasUnpickler.load_from_file(
            legacy_ats_file_path, cls.MODULE_ALIASES, cls.CLASS_ALIASES
        )

        return list(map(cls.convert_legacy_string, strings))

    @classmethod
    def convert_legacy_string(cls, legacy_string: LegacyString) -> String:
        """
        Converts a legacy string to the new String class.

        Args:
            legacy_string (LegacyString): Legacy string to convert.

        Returns:
            String: Converted String object.
        """

        return String(
            form_id=legacy_string.form_id,
            editor_id=legacy_string.editor_id,
            index=legacy_string.index,
            type=legacy_string.type,
            original=legacy_string.original_string,
            string=legacy_string.translated_string,
            status=cls.convert_legacy_status(legacy_string.status),
        )

    @classmethod
    def convert_legacy_status(cls, legacy_status: LegacyString.Status) -> String.Status:
        """
        Converts the status of a legacy string to the new String class.

        Args:
            legacy_status (LegacyString.Status): Legacy status to convert.

        Returns:
            String.Status: Converted status.
        """

        return String.Status(legacy_status.value)

    @classmethod
    def save_translation_strings(
        cls, translation_folder: Path, strings: dict[str, list[String]]
    ) -> None:
        """
        Saves the strings for a translation to the specified folder.

        Args:
            translation_folder (Path): Path to the folder to save the strings to.
            strings (dict[str, list[String]]): Map of mod file names to their list of strings.
        """

        translation_folder.mkdir(parents=True, exist_ok=True)

        for modfile_name, modfile_strings in strings.items():
            cls.save_strings_to_json_file(
                translation_folder / f"{modfile_name}.json", modfile_strings
            )

    @classmethod
    def save_strings_to_json_file(
        cls, json_file_path: Path, strings: list[String], indent: Optional[int] = None
    ) -> None:
        """
        Saves strings to a JSON file.

        Args:
            json_file_path (Path): Path to the JSON file.
            strings (list[String]): List of strings.
            indent (Optional[int], optional): Indentation level. Defaults to None.
        """

        json_file_path.write_bytes(StringListModel.dump_json(strings, indent=indent))
