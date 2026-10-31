"""
Copyright (c) Cutleast
"""

import logging
import time
from pathlib import Path
from typing import Optional, TypeAlias

import numpy as np
from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.core.utilities.reference_dict import ReferenceDict
from cutleast_core_lib.ui.progress.display import ProgressDisplay
from PySide6.QtCore import QObject
from rapidfuzz import process, utils

from core.database.database import TranslationDatabase
from core.database.translation import Translation
from core.file_types.file_type import FileType
from core.mod_file.context import ModFileContext
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod_instance import ModInstance
from core.string.placeholder_parser import PlaceholderParser
from core.string.string_status import StringStatus
from core.string.types import String, StringList
from core.translation_context.context import TranslationContext
from core.translation_context.reference_resolver import ReferenceResolver
from core.translation_context.similar_string import SimilarString

FuzzyKey: TypeAlias = tuple[Translation, Path, String]


class ContextBuilder(QObject):
    """
    Builds translation contexts for strings.
    """

    MAX_FUZZY_LENGTH: int = 100
    """
    Maximum number of characters used for fuzzy matching. Strings longer than this are
    ignored.
    """

    MAX_SIMILAR_STRINGS: int = 5
    """Maximum number of similar strings returned per query."""

    FUZZY_SCORE_CUTOFF: int = 80
    """Minimum fuzzy matching score."""

    FUZZY_BATCH_SIZE: int = 256
    """Size of each fuzzy search batch."""

    FUZZY_WORKERS: int = 8
    """Number of workers used by the fuzzy searcher."""

    __database: TranslationDatabase
    __mod_instance: Optional[ModInstance]
    __resolver: Optional[ReferenceResolver]

    log: logging.Logger = logging.getLogger("ContextBuilder")

    def __init__(
        self, database: TranslationDatabase, mod_instance: Optional[ModInstance] = None
    ) -> None:
        """
        Args:
            database (TranslationDatabase): The loaded translation database.
            mod_instance (Optional[ModInstance]):
                The loaded mod instance for mod file-specific context.
        """

        super().__init__()

        self.__database = database
        self.__mod_instance = mod_instance
        self.__resolver = None

    def build_single_context(
        self, string: String, mod_file_path: Path, all_strings: dict[Path, StringList]
    ) -> TranslationContext:
        """
        Builds the context for a single string.

        Args:
            string (String): The string to build the context for.
            mod_file_path (Path): The mod file path that the string originates from.
            all_strings (dict[Path, StringList]):
                All strings of the edited translation per mod file path.

        Returns:
            TranslationContext: The translation context for the string.
        """

        return self.__build({mod_file_path: [string]}, all_strings)[string]

    def build_context(
        self, strings: dict[Path, StringList], pdisplay: Optional[ProgressDisplay] = None
    ) -> ReferenceDict[String, TranslationContext]:
        """
        Builds translation contexts for all strings of a translation.

        Args:
            strings (dict[Path, StringList]):
                All strings of the edited translation per mod file path.
            pdisplay (Optional[ProgressDisplay], optional):
                Optional progress display. Defaults to None.

        Raises:
            TaskCancelledError: If the operation is cancelled.

        Returns:
            ReferenceDict[String, TranslationContext]:
                Dictionary with translation contexts for each string.
        """

        return self.__build(strings, strings, pdisplay)

    def __build(
        self,
        strings: dict[Path, StringList],
        all_strings: dict[Path, StringList],
        pdisplay: Optional[ProgressDisplay] = None,
    ) -> ReferenceDict[String, TranslationContext]:
        """
        Builds translation contexts for multiple strings.

        Args:
            strings (dict[Path, StringList]):
                Strings to build the contexts for per mod file path.
            all_strings (dict[Path, StringList]):
                All strings of the edited translation per mod file path.
            pdisplay (Optional[ProgressDisplay], optional):
                Optional progress display. Defaults to None.

        Raises:
            TaskCancelledError: If the operation is cancelled.

        Returns:
            ReferenceDict[String, TranslationContext]:
                Dictionary with translation contexts for each string.
        """

        start: float = time.time()

        items: list[String] = [
            string
            for mod_file_strings in strings.values()
            for string in mod_file_strings
        ]

        if not items:
            return ReferenceDict()

        choices: dict[FuzzyKey, str] = self.__get_choices()
        query_strings: list[String] = [
            string
            for string in items
            if len(string.original) <= ContextBuilder.MAX_FUZZY_LENGTH
        ]
        similar_strings: ReferenceDict[String, list[SimilarString]] = (
            self.__search_similar_batch(query_strings, choices, pdisplay)
        )

        mod_file_contexts: ReferenceDict[String, ModFileContext] = ReferenceDict()
        for index, (mod_file_path, mod_file_strings) in enumerate(
            strings.items(), start=1
        ):
            mod_file_contexts.update(
                self.__get_mod_file_contexts(
                    mod_file_path, mod_file_strings, all_strings
                )
            )

            if pdisplay is not None:
                pdisplay.updateMainProgress(
                    ProgressUpdate(
                        status_text=self.tr("Building translation context..."),
                        value=index,
                        maximum=len(strings),
                    )
                )

        result: ReferenceDict[String, TranslationContext] = ReferenceDict()
        for string in items:
            result[string] = TranslationContext(
                similar_strings=similar_strings.get(string, []),
                mod_file_context=mod_file_contexts.get(string, ModFileContext()),
                placeholders=PlaceholderParser.parse(string.original),
            )

        duration: float = time.time() - start

        self.log.debug(
            f"Built context for {len(result)} string(s) in {duration:.2f} second(s)."
        )

        return result

    def __search_similar_batch(
        self,
        strings: list[String],
        choices: dict[FuzzyKey, str],
        pdisplay: Optional[ProgressDisplay] = None,
    ) -> ReferenceDict[String, list[SimilarString]]:
        """
        Searches similar strings in cancellable batches.

        Args:
            strings (list[String]): Query strings.
            choices (dict[FuzzyKey, str]):
                Candidates used for fuzzy matching.
            pdisplay (Optional[ProgressDisplay], optional):
                Optional progress display. Defaults to None.

        Raises:
            TaskCancelledError:
                If the operation is cancelled through the progress display.

        Returns:
            ReferenceDict[String, list[SimilarString]]:
                Up to five similar strings for each query.
        """

        start: float = time.time()

        # Normalizing once up front avoids normalizing every choice again per batch.
        # Choices consisting only of punctuation would match each other perfectly.
        processed_choices: dict[FuzzyKey, str] = {
            key: processed_choice
            for key, choice in choices.items()
            if (processed_choice := utils.default_process(choice))
        }
        choice_keys: list[FuzzyKey] = list(processed_choices)
        choice_values: list[str] = list(processed_choices.values())

        result: ReferenceDict[String, list[SimilarString]] = ReferenceDict()
        total: int = len(strings)

        if pdisplay is not None:
            pdisplay.updateMainProgress(
                ProgressUpdate(
                    status_text=self.tr("Searching similar strings..."),
                    value=0,
                    maximum=total,
                )
            )

        for batch_start in range(0, total, ContextBuilder.FUZZY_BATCH_SIZE):
            batch_strings: StringList = strings[
                batch_start : batch_start + ContextBuilder.FUZZY_BATCH_SIZE
            ]

            queries: list[str] = [
                utils.default_process(string.original[: ContextBuilder.MAX_FUZZY_LENGTH])
                for string in batch_strings
            ]

            scores: np.ndarray = process.cdist(
                queries,
                choice_values,
                score_cutoff=ContextBuilder.FUZZY_SCORE_CUTOFF,
                dtype=np.uint8,
                workers=ContextBuilder.FUZZY_WORKERS,
            )

            for query_index, string in enumerate(batch_strings):
                row: np.ndarray = scores[query_index]

                matching_indices: np.ndarray = np.flatnonzero(
                    row >= ContextBuilder.FUZZY_SCORE_CUTOFF
                )
                sorted_indices: np.ndarray = matching_indices[
                    np.argsort(row[matching_indices])[::-1]
                ]

                similar_strings: list[SimilarString] = []
                for candidate_index in sorted_indices:
                    translation, mod_file, candidate = choice_keys[int(candidate_index)]

                    if candidate.id == string.id:
                        continue

                    similar_strings.append(
                        SimilarString(
                            string=candidate,
                            score=float(row[candidate_index]),
                            translation=translation,
                            mod_file=mod_file,
                        )
                    )

                    if len(similar_strings) >= ContextBuilder.MAX_SIMILAR_STRINGS:
                        break

                result[string] = similar_strings

            processed: int = min(batch_start + len(batch_strings), total)

            if pdisplay is not None:
                pdisplay.updateMainProgress(
                    ProgressUpdate(
                        status_text=self.tr("Searching similar strings..."),
                        value=processed,
                        maximum=total,
                    )
                )

        duration: float = time.time() - start

        self.log.debug(
            f"Found similar strings for {len(strings)} query string(s) from "
            f"{len(choices)} candidate(s) in {duration:.2f} second(s)."
        )

        return result

    def __get_mod_file_contexts(
        self,
        mod_file_path: Path,
        strings: StringList,
        all_strings: dict[Path, StringList],
    ) -> ReferenceDict[String, ModFileContext]:
        """
        Gets the mod file-specific contexts for strings of a single mod file. Reads the
        original mod file for additional context if it is available in the mod instance
        or in the game's "Data" folder.

        Args:
            mod_file_path (Path): Mod file path containing the strings.
            strings (StringList): Strings to get the contexts for.
            all_strings (dict[Path, StringList]):
                All strings of the edited translation per mod file path.

        Returns:
            ReferenceDict[String, ModFileContext]: The context for each string.
        """

        file_type: Optional[FileType] = next(
            (
                file_type
                for file_type in FileType
                if strings and isinstance(strings[0], file_type.get_string_type_cls())
            ),
            None,
        )
        if file_type is None:
            return ReferenceDict()

        original_mod_file: Optional[ModFile] = self.__get_original_mod_file(
            mod_file_path, file_type
        )
        if original_mod_file is not None:
            return original_mod_file.get_contexts(
                strings, all_strings, self.__get_resolver(all_strings)
            )

        return file_type.get_file_type_cls().get_string_contexts(
            mod_file_path, strings, all_strings
        )

    def __get_resolver(self, all_strings: dict[Path, StringList]) -> ReferenceResolver:
        """
        Gets the resolver for referenced records, which is created on first use.

        Args:
            all_strings (dict[Path, StringList]):
                All strings of the edited translation per mod file path.

        Returns:
            ReferenceResolver: The resolver.
        """

        if self.__resolver is None:
            # The edited strings take precedence over their copies in the database.
            self.__resolver = ReferenceResolver(
                [all_strings]
                + [
                    translation.strings
                    for translation in self.__database.user_translations
                ]
                + [self.__database.vanilla_translation.strings]
            )

        return self.__resolver

    def __get_original_mod_file(
        self, mod_file_path: Path, file_type: FileType
    ) -> Optional[ModFile]:
        """
        Gets the original mod file from the loaded mod instance. Base game files are
        taken from the game's "Data" folder as they are not part of any mod.

        Args:
            mod_file_path (Path): Path of the mod file.
            file_type (FileType): Type of the mod file.

        Returns:
            Optional[ModFile]: The original mod file if it is available.
        """

        if self.__mod_instance is None:
            return None

        mod_file: Optional[ModFile] = self.__mod_instance.get_modfile(
            mod_file_path,
            ignore_states=[
                state
                for state in TranslationStatus
                if state
                not in [
                    TranslationStatus.TranslationInstalled,
                    TranslationStatus.TranslationIncomplete,
                ]
            ],
        )

        game_folder: Optional[Path] = self.__mod_instance.game_folder
        if mod_file is None and game_folder is not None:
            base_game_file_path: Path = game_folder / "Data" / mod_file_path
            if base_game_file_path.is_file():
                mod_file = file_type.get_file_type_cls()(
                    name=base_game_file_path.name, full_path=base_game_file_path
                )

        return mod_file

    def __get_choices(self) -> dict[FuzzyKey, str]:
        """
        Collects candidates for fuzzy matching.

        Returns:
            dict[FuzzyKey, str]: Dictionary containing the fuzzy matching candidates.
        """

        translations: list[Translation] = [
            self.__database.vanilla_translation
        ] + self.__database.user_translations

        key: tuple[str, str]
        seen: set[tuple[str, str]] = set()
        choices: dict[FuzzyKey, str] = {}
        for translation in translations:
            for mod_file_path, strings in translation.strings.items():
                for string in strings:
                    if (
                        string.status >= StringStatus.TranslationRequired
                        or string.string is None
                        or string.string == string.original
                    ):
                        continue

                    key = string.original, string.string
                    if (
                        key in seen
                        or len(string.original) > ContextBuilder.MAX_FUZZY_LENGTH
                    ):
                        continue

                    seen.add(key)

                    choices[(translation, mod_file_path, string)] = string.original

        return choices
