"""
Copyright (c) Cutleast
"""

import logging
import re
from copy import copy, deepcopy
from pathlib import Path
from typing import Optional

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.ui.progress.display import ProgressDisplay
from PySide6.QtCore import QObject, Signal

from core.database.database import TranslationDatabase
from core.database.translation import Translation
from core.string.string_status import StringStatus
from core.string.types import String, StringList
from core.translator.service import TranslatorService
from core.translator.translator import Translator
from core.utilities.game_language import GameLanguage


class Editor(QObject):
    """
    Class for editing a translation.
    """

    strings_changed = Signal(object)
    """
    Signal emitted when any of the strings in the translation change.

    Args:
        StringList: The list of strings that changed.
    """

    __language: GameLanguage
    __database: TranslationDatabase
    __translator_service: TranslatorService

    __translation: Translation
    __strings_cache: dict[Path, StringList]
    """
    Stores a deep copy of the strings in the translation.
    """

    __changes_pending: bool

    log: logging.Logger = logging.getLogger("Editor")

    def __init__(
        self,
        translation: Translation,
        language: GameLanguage,
        database: TranslationDatabase,
        translator_service: TranslatorService,
    ) -> None:
        """
        Args:
            translation (Translation): The translation to edit.
            language (GameLanguage): The language of the translation.
            database (TranslationDatabase): The translation database.
            translator_service (TranslatorService): The translator service.
        """

        super().__init__()

        self.__translation = translation

        self.__language = language
        self.__database = database
        self.__translator_service = translator_service

        # Make a deep copy to prevent immediately modifying the translation
        self.__strings_cache = deepcopy(self.__translation.strings)

        self.__changes_pending = False

        self.strings_changed.connect(lambda _: self.__on_change())

    def save(self) -> None:
        """
        Saves changes to the translation.
        """

        self.__translation.strings = self.__strings_cache
        self.__translation.save()

        self.log.info(f"Saved translation '{self.__translation.name}'.")
        self.__changes_pending = False

    def __on_change(self, changes_pending: bool = True) -> None:
        self.__changes_pending = changes_pending

    @property
    def changes_pending(self) -> bool:
        """
        Whether there are unsaved changes.
        """

        return self.__changes_pending

    @property
    def strings(self) -> dict[Path, StringList]:
        """
        Map of plugin names to their list of strings.
        Returns their current editing state.
        """

        return copy(self.__strings_cache)

    @property
    def all_strings(self) -> StringList:
        """
        List of all strings.
        """

        return [
            string for strings in self.__strings_cache.values() for string in strings
        ]

    def get_string_states_summary(
        self, strings: Optional[StringList] = None
    ) -> dict[StringStatus, int]:
        """
        Get a summary of string states.

        Args:
            strings (Optional[StringList], optional):
                List of strings to summarize. If None, summarizes all strings. Defaults
                to None.

        Returns:
            dict[StringStatus, int]:
                Dictionary of string states and number of strings in each state
        """

        if strings is None:
            strings = self.all_strings

        return {
            state: len([string for string in strings if string.status == state])
            for state in StringStatus
        }

    def set_status(self, strings: StringList, status: StringStatus) -> None:
        """
        Sets the status of a list of strings.

        Args:
            strings (StringList): List of strings
            status (Status): The status to set
        """

        for string in strings:
            string.status = status

        self.strings_changed.emit(strings)
        self.log.info(f"Updated status for {len(strings)} string(s).")

    def translate_with_api(
        self, strings: StringList, pdisplay: Optional[ProgressDisplay]
    ) -> None:
        """
        Translates a list of strings with a translator API.

        Args:
            strings (StringList): List of strings
            pdisplay (Optional[ProgressDisplay]):
                Optional progress display, defaults to None.
        """

        if pdisplay is not None:
            pdisplay.updateMainProgress(
                ProgressUpdate(status_text=self.tr("Translating with API..."))
            )

        self.log.info(f"Translating {len(strings)} string(s) with API...")

        translator: Translator = self.__translator_service.get_translator()

        self.log.info(f"Used translator API: {translator.__class__.__name__}")

        texts: list[str] = [selected_string.original for selected_string in strings]
        result: dict[str, str] = translator.mass_translate(texts, self.__language)

        for string in strings:
            string.string = result[string.original]
            string.status = StringStatus.TranslationIncomplete

        self.strings_changed.emit(strings)
        self.log.info("API translation complete.")

    def apply_regex(
        self, strings: StringList, replace_text: str, pattern: re.Pattern
    ) -> int:
        """
        Applies a regex to a list of strings.

        Args:
            strings (StringList): List of strings
            replace_text (str): Replacer text
            pattern (re.Pattern): Regex pattern

        Returns:
            int: Number of strings modified
        """

        self.log.info(f"Applying regex to {len(strings)} string(s)...")

        modified_strings: StringList = []
        for string in strings:
            src: str = string.string if string.string is not None else string.original
            res: str = pattern.sub(replace_text, src)
            string.string = res

            if src != string.string:
                string.status = StringStatus.TranslationIncomplete
                modified_strings.append(string)

        self.strings_changed.emit(modified_strings)
        self.log.info("Regex applied.")

        return len(modified_strings)

    def apply_database(self, strings: StringList) -> int:
        """
        Applies database to a list of strings.

        Args:
            strings (StringList): List of strings

        Returns:
            int: Number of strings modified
        """

        self.log.info(f"Applying database to {len(strings)} string(s)...")

        database_originals: dict[str, String] = {
            string.original: string for string in self.__database.strings
        }
        database_strings: dict[str, String] = {
            string.id: string for string in self.__database.strings
        }

        modified_strings: StringList = []
        for string in strings:
            if string.id in database_strings:
                string.string = database_strings[string.id].string
                string.status = StringStatus.TranslationComplete
                modified_strings.append(string)

            elif string.original in database_originals:
                string.string = database_originals[string.original].string
                string.status = StringStatus.TranslationIncomplete
                modified_strings.append(string)

        self.strings_changed.emit(modified_strings)
        self.log.info("Database applied.")

        return len(modified_strings)

    def apply_to_matching_strings(self, original: str, translation: str) -> int:
        """
        Applies translation to strings that are matching.

        Args:
            original (str): The original string
            translation (str): The translation

        Returns:
            int: Number of strings modified
        """

        modified_strings: StringList = []
        for string in self.all_strings:
            if (
                string.original == original
                and string.status != StringStatus.TranslationComplete
            ):
                string.string = translation
                string.status = StringStatus.TranslationIncomplete
                modified_strings.append(string)

        self.strings_changed.emit(modified_strings)
        self.log.info(f"Applied translation to {len(modified_strings)} string(s).")

        return len(modified_strings)

    def reset_strings(self, strings: StringList) -> None:
        """
        Resets the translation and the status of a list of strings.

        Args:
            strings (StringList): List of strings
        """

        self.log.info(f"Resetting {len(strings)} string(s)...")

        for string in strings:
            string.string = None
            string.status = StringStatus.TranslationRequired

        self.strings_changed.emit(strings)
        self.log.info("Strings reset.")
