"""
Copyright (c) Cutleast
"""

import logging
import re
from copy import copy
from pathlib import Path
from typing import Optional

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.core.utilities.exceptions import TaskCancelledError
from cutleast_core_lib.core.utilities.reference_dict import ReferenceDict
from cutleast_core_lib.core.utilities.typing_utils import coalesce
from cutleast_core_lib.ui.progress.display import ProgressDisplay
from PySide6.QtCore import QObject, Signal

from core.config.translator_config import TranslatorConfig
from core.database.database import TranslationDatabase
from core.database.translation import Translation
from core.editor.models.diagnostics import TranslationDiagnostics
from core.mod_instance.mod_instance import ModInstance
from core.string.string_status import StringStatus
from core.string.types import String
from core.translation_context.builder import ContextBuilder
from core.translation_context.context import TranslationContext
from core.translator.models.request import TranslationRequest
from core.translator.models.result import TranslationResult
from core.translator.service import TranslatorService
from core.translator.translator import Translator
from core.utilities.game_language import GameLanguage

from .models import EditorString
from .validator import TranslationValidator


class Editor(QObject):
    """
    Class for editing a translation.
    """

    strings_changed = Signal(object)
    """
    Signal emitted when any of the strings in the translation change.

    Args:
        list[EditorString]: The list of strings that changed.
    """

    strings_modified = Signal()
    """Signal emitted when any string is modified."""

    MAX_PROGRESS_TEXT_LENGTH: int = 50
    """Maximum length of a text that is displayed in a progress bar."""

    DIAGNOSTICS_STATUS: list[StringStatus] = [StringStatus.TranslationIncomplete]
    """List of string status, that qualify a string for diagnostics."""

    __language: GameLanguage
    __database: TranslationDatabase
    __translator_service: TranslatorService
    __context_builder: ContextBuilder
    __validator: TranslationValidator

    __translation: Translation
    __strings: dict[Path, list[EditorString]]

    __changes_pending: bool

    log: logging.Logger = logging.getLogger("Editor")

    def __init__(
        self,
        translation: Translation,
        language: GameLanguage,
        database: TranslationDatabase,
        mod_instance: Optional[ModInstance],
        translator_config: TranslatorConfig,
        translator_service: TranslatorService,
        user_data_path: Path,
    ) -> None:
        """
        Args:
            translation (Translation): The translation to edit.
            language (GameLanguage): The language of the translation.
            database (TranslationDatabase): The translation database.
            mod_instance (Optional[ModInstance]): The loaded mod instance.
            translator_config (TranslatorConfig): The translator configuration.
            translator_service (TranslatorService): The translator service.
            user_data_path (Path): The path to the user data directory.
        """

        super().__init__()

        self.__translation = translation

        self.__language = language
        self.__database = database
        self.__translator_service = translator_service
        self.__context_builder = ContextBuilder(
            database, translator_config, mod_instance
        )
        self.__validator = TranslationValidator(user_data_path)

        self.__strings = {
            mod_file_path: [
                EditorString(string=string.model_copy(), mod_file_path=mod_file_path)
                for string in mod_file_strings
            ]
            for mod_file_path, mod_file_strings in translation.strings.items()
        }
        self.__changes_pending = False

        self.__validator.word_added_to_user_dictionary.connect(
            self.__on_word_added_to_user_dict
        )
        self.strings_modified.connect(self.__on_change)

    def save(self) -> None:
        """
        Saves changes to the translation.
        """

        self.__translation.strings = {
            mod_file_path: [string.string for string in strings]
            for mod_file_path, strings in self.__strings.items()
        }
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
    def strings(self) -> dict[Path, list[EditorString]]:
        """
        Map of plugin names to their list of strings.
        Returns their current editing state.
        """

        return copy(self.__strings)

    @property
    def all_strings(self) -> list[EditorString]:
        """
        List of all strings.
        """

        return [string for strings in self.__strings.values() for string in strings]

    def get_string_states_summary(
        self, strings: Optional[list[EditorString]] = None
    ) -> dict[StringStatus, int]:
        """
        Get a summary of string states.

        Args:
            strings (Optional[list[EditorString]], optional):
                List of strings to summarize. If None, summarizes all strings. Defaults
                to None.

        Returns:
            dict[StringStatus, int]:
                Dictionary of string states and number of strings in each state
        """

        if strings is None:
            strings = self.all_strings

        return {
            state: len([string for string in strings if string.string.status == state])
            for state in StringStatus
        }

    def set_status(self, strings: list[EditorString], status: StringStatus) -> None:
        """
        Sets the status of a list of strings.

        Args:
            strings (list[EditorString]): List of strings
            status (Status): The status to set
        """

        for string in strings:
            string.string.status = status
            self.__update_string_diagnostics(string)

        self.strings_changed.emit(strings)
        self.strings_modified.emit()
        self.log.info(f"Updated status for {len(strings)} string(s).")

    def translate_with_api(
        self,
        strings: list[EditorString],
        additional_instructions: Optional[str],
        pdisplay: Optional[ProgressDisplay],
    ) -> None:
        """
        Translates a list of strings with a translator API.

        Args:
            strings (list[EditorString]): Strings to translate.
            additional_instructions (Optional[str]): Additional user instructions.
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

        requests: ReferenceDict[TranslationRequest, EditorString] = ReferenceDict()
        for string in strings:
            request: TranslationRequest = self.__create_api_translation_request(
                string, additional_instructions
            )
            requests[request] = string

        results: Mapping[TranslationRequest, TranslationResult] = (
            translator.batch_translate(list(requests.keys()), pdisplay)
        )

        for request, result in results.items():
            string: EditorString = requests[request]
            string.string.string = result.translated_text
            string.string.status = StringStatus.TranslationIncomplete
            string.diagnostics = None
            self.__update_string_diagnostics(string)
            self.strings_changed.emit(strings)
            self.strings_modified.emit()
            self.log.info("API translation complete.")

    def get_api_translation(
        self,
        string: EditorString,
        additional_instructions: Optional[str],
        pdisplay: Optional[ProgressDisplay] = None,
    ) -> str:
        """
        Requests an API translation for a string without modifying it.

        Args:
            string (EditorString): The string to get an API translation for.
            additional_instructions (Optional[str]): Additional user instructions.
            pdisplay (Optional[ProgressDisplay], optional):
                Optional progress display. Defaults to None.

        Returns:
            str: The translated text returned by the translator API.
        """

        translator: Translator = self.__translator_service.get_translator()

        def update_callback(update: ProgressUpdate) -> None:
            if pdisplay is not None:
                pdisplay.updateMainProgress(update)

        request: TranslationRequest = self.__create_api_translation_request(
            string, additional_instructions
        )
        result: TranslationResult = translator.translate(request, update_callback)
        return result.translated_text

    def __create_api_translation_request(
        self, string: EditorString, additional_instructions: Optional[str] = None
    ) -> TranslationRequest:
        """
        Creates an API translation request for a string. Appends the current translated
        text, if there is one and it differs from the original text.

        Args:
            string (EditorString): The string to create an API translation request for.
            additional_instructions (Optional[str], optional):
                Additional user instructions. Defaults to None.

        Returns:
            TranslationRequest: The created API translation request.
        """

        return TranslationRequest(
            text=string.string.original,
            dst=self.__language,
            context=self.get_string_context(string),
            instructions=additional_instructions,
            old_translation=(
                string.string.string
                if self.__translator_service.get_translator().supports_corrections()
                and string.string.string is not None
                and string.string.string != string.string.original
                else None
            ),
        )

    def set_translated_text(
        self, string: EditorString, translated_text: str, sync_identical: bool
    ) -> None:
        """
        Applies a translated text to a string without changing its status.

        Args:
            string (EditorString): The string to update.
            translated_text (str): The translated text to apply.
            sync_identical (bool): Whether to sync identical strings.
        """

        if string.string.string == translated_text:
            return

        modified_strings: list[EditorString] = [string]
        if sync_identical:
            modified_strings += self.get_sync_candidates(string)

        for modified_string in modified_strings:
            modified_string.string.string = translated_text
            modified_string.diagnostics = None
            self.__update_string_diagnostics(modified_string)

        self.strings_changed.emit(modified_strings)
        self.strings_modified.emit()

    def set_string_status(
        self, string: EditorString, status: StringStatus, sync_identical: bool
    ) -> None:
        """
        Applies a status to a single string. Strings with no translation required get
        their original text as translation and the translation of completed strings is
        also applied to other strings with the same original text.

        Args:
            string (EditorString): The string to update.
            status (StringStatus): The status to apply.
            sync_identical (bool): Whether to sync identical strings.
        """

        if string.string.status == status:
            return

        modified_strings: list[EditorString] = [string]
        if sync_identical:
            modified_strings += self.get_sync_candidates(string)

        for modified_string in modified_strings:
            if status == StringStatus.NoTranslationRequired or (
                status != StringStatus.TranslationRequired
                and modified_string.string.string is None
            ):
                modified_string.string.string = string.string.original

            modified_string.string.status = status
            modified_string.diagnostics = None
            self.__update_string_diagnostics(modified_string)

        self.strings_changed.emit(modified_strings)
        self.strings_modified.emit()

    def apply_regex(
        self, strings: list[EditorString], replace_text: str, pattern: re.Pattern
    ) -> int:
        """
        Applies a regex to a list of strings.

        Args:
            strings (list[EditorString]): List of strings
            replace_text (str): Replacer text
            pattern (re.Pattern): Regex pattern

        Returns:
            int: Number of strings modified
        """

        self.log.info(f"Applying regex to {len(strings)} string(s)...")

        modified_strings: list[EditorString] = []
        for string in strings:
            src: str = coalesce(string.string.string, string.string.original)
            res: str = pattern.sub(replace_text, src)
            string.string.string = res

            if src != string.string.string:
                string.string.status = StringStatus.TranslationIncomplete
                self.__update_string_diagnostics(string)
                modified_strings.append(string)

        self.strings_changed.emit(modified_strings)
        self.strings_modified.emit()
        self.log.info("Regex applied.")

        return len(modified_strings)

    def apply_database(self, strings: list[EditorString]) -> int:
        """
        Applies database to a list of strings.

        Args:
            strings (list[EditorString]): List of strings.

        Returns:
            int: Number of strings modified.
        """

        self.log.info(f"Applying database to {len(strings)} string(s)...")

        database_originals: dict[str, String] = {
            string.original: string
            for string in self.__database.strings
            if string.status
            in [
                StringStatus.NoTranslationRequired,
                StringStatus.TranslationComplete,
                StringStatus.NoneStatus,  # TODO: Remove when implementing issue #137
            ]
        }
        database_strings: dict[str, String] = {
            string.id: string
            for string in self.__database.strings
            if string.status
            in [
                StringStatus.NoTranslationRequired,
                StringStatus.TranslationComplete,
                StringStatus.NoneStatus,  # TODO: Remove when implementing issue #137
            ]
        }

        modified_strings: list[EditorString] = []
        for string in strings:
            if string.string.status not in [
                StringStatus.TranslationRequired,
                StringStatus.TranslationIncomplete,
            ]:
                continue

            if string.string.id in database_strings:
                database_string: String = database_strings[string.string.id]
                if string.string.string != database_string.string:
                    string.string.string = database_string.string
                    string.string.status = (
                        StringStatus.TranslationComplete
                        # TODO: Remove when implementing issue #137
                        if database_string.status == StringStatus.NoneStatus
                        else database_string.status
                    )
                    self.__update_string_diagnostics(string)
                    modified_strings.append(string)

            elif string.string.original in database_originals:
                database_string: String = database_originals[string.string.original]
                if string.string.string != database_string.string:
                    string.string.string = database_string.string
                    string.string.status = StringStatus.TranslationIncomplete
                    self.__update_string_diagnostics(string)
                    modified_strings.append(string)

        if modified_strings:
            self.strings_changed.emit(modified_strings)
            self.strings_modified.emit()

        self.log.info("Database applied.")

        return len(modified_strings)

    def get_sync_candidates(self, string: EditorString) -> list[EditorString]:
        """
        Gets a list of strings whose original text is identical to a given one and whose
        status is not `StringStatus.TranslationComplete`.

        Args:
            string (EditorString): The current string.

        Returns:
            list[EditorString]: The list of synchronization candidates.
        """

        return [
            s
            for s in self.all_strings
            if (
                s is not string and s.string.original == string.string.original
                # and s.string.status != StringStatus.TranslationComplete
            )
        ]

    def reset_string(self, string: EditorString, sync_identical: bool) -> None:
        """
        Resets the translation and the status of a string.

        Args:
            string (EditorString): The string to reset.
            sync_identical (bool): Whether to sync identical strings.
        """

        strings: list[EditorString] = [string]
        if sync_identical:
            strings += self.get_sync_candidates(string)

        self.reset_strings(strings)

    def reset_strings(self, strings: list[EditorString]) -> None:
        """
        Resets the translation and the status of a list of strings.

        Args:
            strings (list[EditorString]): List of strings.
        """

        self.log.info(f"Resetting {len(strings)} string(s)...")

        for string in strings:
            string.string.string = None
            string.string.status = StringStatus.TranslationRequired
            string.diagnostics = None

        self.strings_changed.emit(strings)
        self.strings_modified.emit()
        self.log.info("Strings reset.")

    def initialize(self, pdisplay: Optional[ProgressDisplay] = None) -> None:
        """
        Builds the translation context and runs diagnostics on qualified strings.

        Args:
            pdisplay (Optional[ProgressDisplay], optional):
                Optional progress display. Defaults to None.
        """

        self.build_string_context(pdisplay)
        self.run_string_diagnostics(pdisplay)

    def build_string_context(self, pdisplay: Optional[ProgressDisplay] = None) -> None:
        """
        Builds the translation context for all strings in the translation.

        Args:
            pdisplay (Optional[ProgressDisplay], optional):
                Optional progress display. Defaults to None.
        """

        self.log.info("Building translation context...")

        editor_strings: dict[String, EditorString] = {
            s.string: s for s in self.all_strings
        }

        try:
            contexts: ReferenceDict[String, TranslationContext] = (
                self.__context_builder.build_context(
                    {
                        mod_file_path: [s.string for s in mod_file_strings]
                        for mod_file_path, mod_file_strings in self.strings.items()
                    },
                    pdisplay,
                )
            )

        except TaskCancelledError:
            self.log.info("Cancelled building translation context.")
        else:
            for string, context in contexts.items():
                editor_strings[string].context = context

            self.strings_changed.emit(self.all_strings)

            self.log.info("Translation context complete.")

    def run_string_diagnostics(self, pdisplay: Optional[ProgressDisplay] = None) -> None:
        """
        Runs diagnostics on all qualified strings.

        Args:
            pdisplay (Optional[ProgressDisplay], optional):
                Optional progress display. Defaults to None.
        """

        self.log.info("Running translation diagnostics...")

        if pdisplay is not None:
            pdisplay.updateMainProgress(
                ProgressUpdate(
                    status_text=self.tr("Running translation diagnostics..."),
                    value=0,
                    maximum=0,
                )
            )

        qualified_strings: list[EditorString] = [
            string
            for string in self.all_strings
            if self.__is_qualified_for_diagnostics(string)
        ]

        for s, string in enumerate(qualified_strings):
            if pdisplay is not None:
                pdisplay.updateMainProgress(
                    ProgressUpdate(
                        status_text=(
                            self.tr("Running translation diagnostics...")
                            + f"{s + 1}/{len(qualified_strings)}"
                        ),
                        value=s + 1,
                        maximum=len(qualified_strings),
                    )
                )

            assert string.string.string is not None
            assert string.context is not None

            string.diagnostics = self.__validator.validate_translated_text(
                string.string.original,
                string.string.string,
                self.__language,
                string.context,
            )
            self.strings_changed.emit([string])

        self.log.info(
            f"Run translation diagnostics for {len(qualified_strings)} string(s)."
        )

    def get_string_context(self, string: EditorString) -> TranslationContext:
        """
        Gets the context for a string.

        Args:
            string (EditorString): The edited string.

        Returns:
            TranslationContext: The translation context for the string.
        """

        if string.context is None:
            string.context = self.__context_builder.build_single_context(
                string.string,
                string.mod_file_path,
                {
                    mod_file_path: [s.string for s in mod_file_strings]
                    for mod_file_path, mod_file_strings in self.strings.items()
                },
            )
            self.strings_changed.emit([string])

        return string.context

    def __is_qualified_for_diagnostics(self, string: EditorString) -> bool:
        return (
            string.string.status in Editor.DIAGNOSTICS_STATUS
            and string.string.string is not None
            and string.context is not None
        )

    def __update_string_diagnostics(self, string: EditorString) -> bool:
        """
        Updates the diagnostics for a string.

        Args:
            string (EditorString): The string.

        Returns:
            bool: If the diagnostics for the string have changed.
        """

        if not self.__is_qualified_for_diagnostics(string):
            string.diagnostics = None
            return True

        elif string.diagnostics is None:
            assert string.string.string is not None
            assert string.context is not None

            string.diagnostics = self.__validator.validate_translated_text(
                string.string.original,
                string.string.string,
                self.__language,
                string.context,
            )
            return True

        return False

    def get_string_diagnostics(
        self, string: EditorString
    ) -> Optional[TranslationDiagnostics]:
        """
        Gets the diagnostics for a string.

        Args:
            string (EditorString): The edited string.

        Returns:
            Optional[TranslationDiagnostics]: The diagnostics for the string.
        """

        if self.__update_string_diagnostics(string):
            self.strings_changed.emit([string])

        return string.diagnostics

    def get_editor_string(self, string: String) -> EditorString:
        """
        Gets the editor string object for a string.

        Args:
            string (String): The string.

        Raises:
            KeyError: If the string does not belong to the current translation.

        Returns:
            EditorString: The editor string object.
        """

        editor_strings: ReferenceDict[String, EditorString] = ReferenceDict(
            {s.string: s for s in self.all_strings}
        )

        return editor_strings[string]

    def add_word_to_dict(self, word: str) -> None:
        """
        Reruns the diagnostics of all strings that reported the specified word as
        unknown, for example after it was added to the dictionary.

        Args:
            word (str): The word that is now known.
        """

        self.__validator.add_word_to_user_dictionary(word, self.__language)

    def __on_word_added_to_user_dict(self, word: str) -> None:
        affected_strings: list[EditorString] = [
            string
            for string in self.all_strings
            if string.diagnostics is not None
            and word in string.diagnostics.unknown_words
        ]

        for string in affected_strings:
            string.diagnostics = None
            self.__update_string_diagnostics(string)

        if affected_strings:
            self.strings_changed.emit(affected_strings)
