"""
Copyright (c) Cutleast
"""

import logging
import re
from pathlib import Path
from typing import Optional

import jstyleson as json
from PySide6.QtCore import QObject, Signal

from app_context import AppContext
from core.database.database import TranslationDatabase
from core.database.string import String
from core.database.translation import Translation
from core.translator_api.translator import Translator
from ui.widgets.loading_dialog import LoadingDialog


class Editor(QObject):
    """
    Class for editing a translation.
    """

    log: logging.Logger = logging.getLogger("Editor")

    __translation: Translation
    __current_plugin: Optional[str]
    __strings_cache: dict[str, list[String]]
    """
    Stores a deep copy of the strings in the translation.
    """

    update_signal = Signal()
    """
    This signal gets emitted when any of the strings in the translation change.
    """

    def __init__(self, translation: Translation, current_plugin: Optional[str] = None):
        super().__init__()

        self.__translation = translation
        self.__current_plugin = current_plugin

        # TODO: Make a deep copy to prevent immediately modifying the translation
        # This seems to break the link to the strings widget
        # self.__strings_cache = deepcopy(self.__translation.strings)
        self.__strings_cache = self.__translation.strings

    def set_current_plugin(self, plugin_name: str) -> None:
        """
        Sets the current plugin.
        """

        self.__current_plugin = plugin_name

    def save(self) -> None:
        """
        Saves changes to the translation.
        """

        self.__translation.strings = self.__strings_cache
        self.__translation.save_translation()

        self.log.info(f"Saved translation {self.__translation.name!r}.")

        self.update_signal.emit()

    @property
    def strings(self) -> list[String]:
        """
        List of currently relevant strings.
        (All strings if no plugin is selected, otherwise only strings
        from the selected plugin)
        """

        if self.__current_plugin is None:
            return [
                string
                for strings in self.__strings_cache.values()
                for string in strings
            ]
        else:
            return self.__strings_cache[self.__current_plugin]

    def __get_string_from_id(self, string_id: str) -> Optional[String]:
        target_string: Optional[String] = None

        strings: list[String]
        if self.__current_plugin is None:
            strings = [
                string
                for strings in self.__translation.strings.values()
                for string in strings
            ]
        else:
            strings = self.__translation.strings[self.__current_plugin]

        for string in strings:
            if string.id == string_id:
                target_string = string
                break

        return target_string

    def __get_strings_from_ids(self, string_ids: list[str]) -> list[String]:
        return [
            _string
            for string_id in string_ids
            if (_string := self.__get_string_from_id(string_id)) is not None
        ]

    def set_status(self, string_ids: list[str], status: String.Status) -> None:
        """
        Sets the status of a list of strings.

        Args:
            string_ids (list[str]): List of string ids
            status (String.Status): The status to set
        """

        for string in self.__get_strings_from_ids(string_ids):
            if string is not None:
                string.status = status

        self.update_signal.emit()
        self.log.info(f"Updated status for {len(string_ids)} string(s).")

    def translate_with_api(
        self, string_ids: list[str], ldialog: Optional[LoadingDialog]
    ) -> None:
        """
        Translates a list of strings with a translator API.

        Args:
            string_ids (list[str]): List of string ids
            ldialog (Optional[LoadingDialog]): Optional loading dialog, defaults to None
        """

        if ldialog is not None:
            ldialog.updateProgress(text1=self.tr("Translating with API..."))

        strings: list[String] = self.__get_strings_from_ids(string_ids)

        self.log.info(f"Translating {len(strings)} string(s) with API...")

        texts: list[str] = [
            selected_string.original_string for selected_string in strings
        ]
        translator: Translator = AppContext.get_app().translator
        src: str = "English"
        dst: str = AppContext.get_app().user_config.language
        result: dict[str, str] = translator.mass_translate(texts, src, dst)

        for string in strings:
            string.translated_string = result[string.original_string]
            string.status = String.Status.TranslationIncomplete

        self.update_signal.emit()
        self.log.info("API translation complete.")

    def apply_regex(
        self, string_ids: list[str], replace_text: str, pattern: re.Pattern
    ) -> int:
        """
        Applies a regex to a list of strings.

        Args:
            string_ids (list[str]): List of string ids
            replace_text (str): Replacer text
            pattern (re.Pattern): Regex pattern

        Returns:
            int: Number of strings modified
        """

        self.log.info(f"Applying regex to {len(string_ids)} string(s)...")

        modified_strings: int = 0
        for string in self.__get_strings_from_ids(string_ids):
            src: str = string.translated_string or string.original_string
            res: str = pattern.sub(replace_text, src)
            string.translated_string = res

            if src != string.translated_string:
                string.status = String.Status.TranslationIncomplete
                modified_strings += 1

        self.update_signal.emit()
        self.log.info("Regex applied.")

        return modified_strings

    def apply_database(self, string_ids: list[str]) -> int:
        """
        Applies database to a list of strings.

        Args:
            string_ids (list[str]): List of string ids

        Returns:
            int: Number of strings modified
        """

        self.log.info(f"Applying database to {len(string_ids)} string(s)...")

        database: TranslationDatabase = AppContext.get_app().database

        database_originals: dict[str, String] = {
            string.original_string: string for string in database.strings
        }
        database_strings: dict[str, String] = {
            string.id: string for string in database.strings
        }

        modified_strings: int = 0
        for string in self.__get_strings_from_ids(string_ids):
            if string.id in database_strings:
                string.translated_string = database_strings[string.id].translated_string
                string.status = String.Status.TranslationComplete
                modified_strings += 1

            elif string.original_string in database_originals:
                string.translated_string = database_originals[
                    string.original_string
                ].translated_string
                string.status = String.Status.TranslationIncomplete
                modified_strings += 1

        self.update_signal.emit()
        self.log.info("Database applied.")

        return modified_strings

    def apply_to_matching_strings(self, original: str, translation: str) -> int:
        """
        Applies translation to strings that are matching.

        Args:
            original (str): The original string
            translation (str): The translation

        Returns:
            int: Number of strings modified
        """

        modified_strings: int = 0
        for string in self.strings:
            if (
                string.original_string == original
                and string.status != String.Status.TranslationComplete
            ):
                string.translated_string = translation
                string.status = String.Status.TranslationIncomplete
                modified_strings += 1

        self.update_signal.emit()
        self.log.info(f"Applied translation to {modified_strings} string(s).")

        return modified_strings

    def reset_strings(self, string_ids: list[str]) -> None:
        """
        Resets the translation and the status of a list of strings.

        Args:
            string_ids (list[str]): List of string ids
        """

        self.log.info(f"Resetting {len(string_ids)} string(s)...")

        for string in self.__get_strings_from_ids(string_ids):
            string.translated_string = None
            string.status = String.Status.TranslationRequired

        self.update_signal.emit()
        self.log.info("Strings reset.")

    def import_legacy_dsd_translation(self, dsd_file: Path) -> int:
        """
        Imports a legacy (pre-v1.1) DSD translation by overwriting the current translation.

        Args:
            dsd_file (Path): Path to DSD file

        Returns:
            int: Number of strings modified
        """

        self.log.info(f"Importing legacy translation from {str(dsd_file)!r}...")

        with dsd_file.open(encoding="utf8") as file:
            legacy_strings: list[dict] = json.load(file)

        self.log.debug(f"Found {len(legacy_strings)} string(s) in legacy translation.")

        translation_strings: dict[str, list[String]] = {}

        for string in self.strings:
            translation_strings.setdefault(string.original_string, []).append(string)

        strings_modified: int = 0
        for legacy_string in legacy_strings:
            original = legacy_string.get("original")
            translated = legacy_string.get("string")

            if original is None or translated is None:
                continue

            matching_strings: Optional[list[String]] = translation_strings.get(original)

            if matching_strings is None:
                continue

            for matching_string in matching_strings:
                matching_string.translated_string = translated

                if (
                    legacy_string.get("type") == matching_string.type
                    and legacy_string.get("editor_id") == matching_string.editor_id
                    and legacy_string.get("index") == matching_string.index
                ):
                    legacy_status = String.Status.get(legacy_string.get("status") or "")

                    if legacy_status is not None:
                        matching_string.status = legacy_status
                    else:
                        matching_string.status = String.Status.TranslationComplete

            strings_modified += 1

        self.update_signal.emit()
        self.log.info("Legacy translation imported.")

        return strings_modified
