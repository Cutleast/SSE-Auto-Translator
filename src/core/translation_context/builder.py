"""
Copyright (c) Cutleast
"""

import logging
import time
from pathlib import Path
from typing import Optional, TypeAlias

import numpy as np
from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.ui.progress.display import ProgressDisplay
from PySide6.QtCore import QObject
from rapidfuzz import fuzz, process

from core.database.database import TranslationDatabase
from core.database.translation import Translation
from core.mod_file.context import ModFileContext
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod_instance import ModInstance
from core.string.string_status import StringStatus
from core.string.types import String, StringList
from core.translation_context.context import TranslationContext
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

    FUZZY_BATCH_SIZE: int = 32
    """Size of each fuzzy search batch."""

    FUZZY_WORKERS: int = 8
    """Number of workers used by the fuzzy searcher."""

    __database: TranslationDatabase
    __mod_instance: Optional[ModInstance]

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

    def build_single_context(
        self, string: String, mod_file_path: Path
    ) -> TranslationContext:
        """
        Builds the context for a single string.

        Args:
            string (String): The string to build the context for.
            mod_file_path (Path): The mod file path that the string originates from.

        Returns:
            TranslationContext: The translation context for the string.
        """

        return self.build_context({mod_file_path: [string]})[string]

    def build_context(
        self, strings: dict[Path, StringList], pdisplay: Optional[ProgressDisplay] = None
    ) -> dict[String, TranslationContext]:
        """
        Builds translation contexts for multiple strings.

        Args:
            strings (dict[Path, StringList]):
                Dictionary with string lists per mod file path.
            pdisplay (Optional[ProgressDisplay], optional):
                Optional progress display. Defaults to None.

        Raises:
            TaskCancelledError: If the operation is cancelled.

        Returns:
            dict[String, TranslationContext]:
                Dictionary with translation contexts for each string.
        """

        start: float = time.time()

        items: list[tuple[Path, String]] = [
            (mod_file_path, string)
            for mod_file_path, mod_file_strings in strings.items()
            for string in mod_file_strings
        ]

        if not items:
            return {}

        choices: dict[FuzzyKey, str] = self.__get_choices()
        query_strings: list[String] = [
            string
            for _, string in items
            if len(string.original) <= ContextBuilder.MAX_FUZZY_LENGTH
        ]
        similar_strings: dict[String, list[SimilarString]] = self.__search_similar_batch(
            query_strings, choices, pdisplay
        )

        result: dict[String, TranslationContext] = {}
        for index, (mod_file_path, string) in enumerate(items, start=1):
            mod_file_context: Optional[ModFileContext] = self.__get_mod_file_context(
                string, mod_file_path
            )

            result[string] = TranslationContext(
                similar_strings=similar_strings.get(string, []),
                mod_file_context=mod_file_context,
            )

            if pdisplay is not None:
                pdisplay.updateMainProgress(
                    ProgressUpdate(
                        status_text=self.tr("Building translation context..."),
                        value=index,
                        maximum=len(items),
                    )
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
    ) -> dict[String, list[SimilarString]]:
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
            dict[String, list[SimilarString]]:
                Up to five similar strings for each query.
        """

        start: float = time.time()

        choice_keys: list[FuzzyKey] = list(choices)
        choice_values: list[str] = list(choices.values())

        result: dict[String, list[SimilarString]] = {}
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
                string.original[: ContextBuilder.MAX_FUZZY_LENGTH]
                for string in batch_strings
            ]

            scores: np.ndarray = process.cdist(
                queries,
                choice_values,
                scorer=fuzz.WRatio,
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

    def __get_mod_file_context(
        self, string: String, mod_file_path: Path
    ) -> Optional[ModFileContext]:
        """
        Gets the mod file-specific context for a string.

        Args:
            string (String): String to get the context for.
            mod_file_path (Path): Mod file path containing the string.

        Returns:
            Optional[ModFileContext]: Mod file context if one is available.
        """

        if self.__mod_instance is None:
            return None

        original_mod_file: Optional[ModFile] = self.__mod_instance.get_modfile(
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

        if original_mod_file is None:
            return None

        return original_mod_file.get_context(string)

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
