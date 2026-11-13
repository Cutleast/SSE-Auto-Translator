"""
Copyright (c) Cutleast
"""

import re
from collections import Counter
from functools import cached_property
from pathlib import Path
from typing import Optional, override

from cutleast_core_lib.core.multithreading.progress import (
    ProgressUpdate,
    UpdateCallback,
    update,
)
from cutleast_core_lib.core.utilities.localized_enum import LocalizedEnum
from cutleast_core_lib.core.utilities.typing_utils import not_none
from cutleast_core_lib.core.utilities.unique import unique
from pydantic import BaseModel
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication
from rapidfuzz import fuzz, process

from core.config.translator_config import TranslatorConfig
from core.database.database import TranslationDatabase
from core.database.translation import Translation
from core.string.string_status import StringStatus
from core.string.types import StringList
from core.utilities.text import (
    find_term,
    get_words,
    normalize_word,
    plain_text,
    remove_non_text,
)


class TranslationGlossary(QObject):
    """
    Aggregates terms from the user-configured translator glossary, a mod and the
    installed database into a list of matching terms sorted descending by priority and
    length.
    """

    MIN_TERM_LENGTH: int = 3
    """Minimum length of a term's plain text. Shorter terms are ignored."""

    MAX_TERM_WORDS: int = 5
    """Maximum number of words of a term. Longer terms are ignored."""

    MAX_EXAMPLE_LENGTH: int = 150
    """Maximum length of an example. Longer ones are too costly for the prompt."""

    class TermSource(LocalizedEnum):
        """
        Source for a glossary term.
        """

        UserGlossary = "user"
        """The term comes from the user-configured glossary."""

        Mod = "mod"
        """The term comes from the currently edited translation."""

        Database = "database"
        """The term comes from the database of installed translations."""

        @override
        def get_localized_name(self) -> str:
            match self:
                case TranslationGlossary.TermSource.UserGlossary:
                    return QApplication.translate("TranslationGlossary", "Custom")
                case TranslationGlossary.TermSource.Mod:
                    return QApplication.translate("TranslationGlossary", "Current mod")
                case TranslationGlossary.TermSource.Database:
                    return QApplication.translate("TranslationGlossary", "Database")

        @override
        def get_localized_description(self) -> str:
            match self:
                case TranslationGlossary.TermSource.UserGlossary:
                    return QApplication.translate(
                        "TranslationGlossary",
                        "The term comes from the user-configured glossary.",
                    )
                case TranslationGlossary.TermSource.Mod:
                    return QApplication.translate(
                        "TranslationGlossary",
                        "The term comes from the currently edited translation.",
                    )
                case TranslationGlossary.TermSource.Database:
                    return QApplication.translate(
                        "TranslationGlossary",
                        "The term comes from the translation database.",
                    )

    class Term(BaseModel, frozen=True):
        """
        A term in the translation glossary with its original term, translated term and
        source.
        """

        original: str
        """The original term."""

        translated: str
        """The translated term."""

        source: TranslationGlossary.TermSource
        """The source of the term."""

        example: Optional[TranslationGlossary.Example] = None
        """An example that demonstrates this term in the original and translated form."""

        @cached_property
        def keys(self) -> frozenset[str]:
            """Normalized words of the original term."""

            return frozenset(
                normalize_word(word.lower()) for word in get_words(self.original)
            )

    class Example(BaseModel, frozen=True):
        """
        An example string serving as reference for the usage of a glossary term.
        """

        original: str
        """The original text."""

        translated: str
        """The translated text."""

        source: TranslationGlossary.TermSource
        """The source of the example."""

    __translator_config: TranslatorConfig
    __database: TranslationDatabase

    __database_glossary: list[Term]
    __database_examples: dict[str, list[Example]]

    def __init__(
        self, translator_config: TranslatorConfig, database: TranslationDatabase
    ) -> None:
        """
        Args:
            translator_config (TranslatorConfig):
                The translator configuration containing the user glossary.
            database (TranslationDatabase): The translation database.
        """

        super().__init__()

        self.__translator_config = translator_config
        self.__database = database

        self.__build_database_glossary()

    def __build_database_glossary(self) -> None:
        self.__database_glossary = []
        database_examples: list[TranslationGlossary.Example] = []

        translations: list[Translation] = self.__database.user_translations + [
            self.__database.vanilla_translation
        ]
        for translation in translations:
            for mod_file_strings in translation.strings.values():
                self.__database_glossary += [
                    TranslationGlossary.Term(
                        original=original,
                        translated=translated,
                        source=TranslationGlossary.TermSource.Database,
                    )
                    for original, translated in self.__get_names_from_string_list(
                        mod_file_strings
                    ).items()
                ]
                database_examples += self.__get_examples_from_string_list(
                    mod_file_strings, TranslationGlossary.TermSource.Database
                )

        self.__database_glossary = unique(self.__database_glossary, lambda t: t.original)
        self.__database_examples = self.__build_example_index(database_examples)

    def __get_names_from_string_list(self, strings: StringList) -> dict[str, str]:
        names: dict[str, Counter[str]] = {}
        for string in strings:
            if (
                (
                    string.status
                    in [
                        StringStatus.NoTranslationRequired,
                        StringStatus.TranslationComplete,
                    ]
                    # the following is a workaround for base game strings as the Vanilla
                    # database strings have no status
                    # TODO: Remove when implementing issue #137
                    or (
                        string.status == StringStatus.NoneStatus
                        and string.string is not None
                    )
                )
                and string.is_name
                and not string.original.islower()
            ):
                original: str = remove_non_text(string.original)
                if len(original) < TranslationGlossary.MIN_TERM_LENGTH or not (
                    0 < len(get_words(original)) <= TranslationGlossary.MAX_TERM_WORDS
                ):
                    continue

                counter: Counter[str] = names.setdefault(original, Counter())
                counter.update([remove_non_text(not_none(string.string))])

        return {name: counter.most_common(1)[0][0] for name, counter in names.items()}

    def __get_examples_from_string_list(
        self, strings: StringList, source: TranslationGlossary.TermSource
    ) -> list[TranslationGlossary.Example]:
        """
        Collects the translated strings that are short enough to serve as examples.
        Names are excluded as they are the terms themselves.

        Args:
            strings (StringList): The strings to collect the examples from.
            source (TranslationGlossary.TermSource): The source of the strings.

        Returns:
            list[TranslationGlossary.Example]: The collected examples.
        """

        return [
            TranslationGlossary.Example(
                original=string.original, translated=string.string, source=source
            )
            for string in strings
            if string.status == StringStatus.TranslationComplete
            and string.string is not None
            and not string.is_name
            and len(string.original) <= TranslationGlossary.MAX_EXAMPLE_LENGTH
        ]

    def __build_example_index(
        self, examples: list[TranslationGlossary.Example]
    ) -> dict[str, list[TranslationGlossary.Example]]:
        """
        Indexes examples by the normalized words of their original text. Very common
        words are left out as they would only waste memory.

        Args:
            examples (list[TranslationGlossary.Example]): The examples to index.

        Returns:
            dict[str, list[TranslationGlossary.Example]]: The examples by index key.
        """

        index: dict[str, list[TranslationGlossary.Example]] = {}
        for example in examples:
            for key in {normalize_word(word) for word in get_words(example.original)}:
                if key:
                    index.setdefault(key, []).append(example)

        return {key: key_examples for key, key_examples in index.items()}

    def __find_example(
        self,
        term: TranslationGlossary.Term,
        text: str,
        index: dict[str, list[TranslationGlossary.Example]],
    ) -> Optional[TranslationGlossary.Example]:
        """
        Finds the example that uses a term most similarly to a text. Only examples whose
        translation contains the translated term are considered, so that examples never
        contradict the glossary.

        Args:
            term (TranslationGlossary.Term): The term to find an example for.
            text (str): The text containing the term.
            index (dict[str, list[TranslationGlossary.Example]]):
                The example index to search.

        Returns:
            Optional[TranslationGlossary.Example]:
                The most similar example or None if there is none.
        """

        keys: list[str] = [
            key for key in map(normalize_word, get_words(term.original)) if key in index
        ]
        if not keys:
            return None

        # The rarest word of the term narrows down the candidates the most
        rarest_key: str = min(keys, key=lambda key: len(index[key]))
        candidates: list[TranslationGlossary.Example] = [
            example
            for example in index[rarest_key]
            if example.original != text
            and example.original != term.original
            and find_term(example.original, term.original, inflected=False) is not None
            and find_term(example.translated, term.translated) is not None
        ]
        if not candidates:
            return None

        best_match: tuple[str, float, int] = process.extractOne(
            text,
            [candidate.original for candidate in candidates],
            scorer=fuzz.token_set_ratio,
        )

        return candidates[best_match[2]]

    def __add_example(
        self,
        term: TranslationGlossary.Term,
        text: str,
        mod_examples: dict[str, list[TranslationGlossary.Example]],
    ) -> TranslationGlossary.Term:
        """
        Adds the most similar example to a term found in a text, preferring examples
        from the currently edited translation over those from the database.

        Args:
            term (TranslationGlossary.Term): The term found in the text.
            text (str): The text containing the term.
            mod_examples (dict[str, list[TranslationGlossary.Example]]):
                The example index of the currently edited translation.

        Returns:
            TranslationGlossary.Term: The term with an example, if one was found.
        """

        example: Optional[TranslationGlossary.Example] = self.__find_example(
            term, text, mod_examples
        )
        if example is None:
            example = self.__find_example(term, text, self.__database_examples)

        if example is None:
            return term

        return term.__replace__(example=example)

    def get_terms_of_string(
        self, text: str, translation_strings: dict[Path, StringList]
    ) -> list[TranslationGlossary.Term]:
        """
        Accumulates a list of all glossary terms that appear in a given text.

        Args:
            text (str): The text to check for glossary terms.
            translation_strings (dict[Path, StringList]):
                The strings of the currently edited translation.

        Returns:
            list[TranslationGlossary.Term]: List of occurring glossary terms.
        """

        return self.get_terms_of_strings([text], translation_strings)[0]

    def get_terms_of_strings(
        self,
        texts: list[str],
        translation_strings: dict[Path, StringList],
        update_callback: Optional[UpdateCallback] = None,
    ) -> list[list[TranslationGlossary.Term]]:
        """
        Accumulates a list of all glossary terms that appear in a list of texts.

        Args:
            texts (list[str]): The texts to check for glossary terms.
            translation_strings (dict[Path, StringList]):
                The strings of the currently edited translation.
            update_callback (Optional[UpdateCallback], optional):
                Optional progress callback. Defaults to None.

        Returns:
            list[list[TranslationGlossary.Term]]: List of occurring glossary terms.
        """

        update(
            update_callback,
            ProgressUpdate(
                status_text=self.tr("Collecting glossary terms..."), value=0, maximum=0
            ),
        )

        glossary: list[TranslationGlossary.Term] = self.get_glossary(translation_strings)
        mod_examples: dict[str, list[TranslationGlossary.Example]] = (
            self.__build_example_index(
                [
                    example
                    for mod_file_strings in translation_strings.values()
                    for example in self.__get_examples_from_string_list(
                        mod_file_strings, TranslationGlossary.TermSource.Mod
                    )
                ]
            )
        )

        term_index: dict[str, list[int]] = TranslationGlossary.__build_term_index(
            glossary
        )

        result: list[list[TranslationGlossary.Term]] = []
        for t, text in enumerate(texts, start=1):
            update(
                update_callback,
                ProgressUpdate(
                    status_text=self.tr("Scanning for glossary terms..."),
                    value=t,
                    maximum=len(texts),
                ),
            )

            search_text: str = plain_text(text.lower())
            text_keys: frozenset[str] = frozenset(
                normalize_word(word.lower()) for word in get_words(search_text)
            )

            matching_terms: list[TranslationGlossary.Term] = []
            for term_id in TranslationGlossary.__get_candidate_ids(
                text_keys, term_index
            ):
                term: TranslationGlossary.Term = glossary[term_id]
                if not term.keys.issubset(text_keys):
                    continue

                match: Optional[re.Match[str]] = find_term(
                    search_text, term.original, inflected=False
                )
                if match is not None:
                    matching_terms.append(self.__add_example(term, text, mod_examples))
                    # remove to avoid overlaps with later (shorter) terms
                    search_text = (
                        search_text[: match.start()]
                        + " " * len(match.group())
                        + search_text[match.end() :]
                    )
                    text_keys = frozenset(
                        normalize_word(word) for word in get_words(search_text)
                    )

            result.append(matching_terms)

        return result

    @staticmethod
    def __build_term_index(
        glossary: list[TranslationGlossary.Term],
    ) -> dict[str, list[int]]:
        """
        Indexes the terms of a glossary by the rarest of their keys, so that only terms
        that can occur in a text have to be checked. Terms without keys are left out as
        they contain no words and can therefore never be found in a text.

        Args:
            glossary (list[TranslationGlossary.Term]): The glossary to index.

        Returns:
            dict[str, list[int]]:
                The positions of the terms in the glossary by index key, in ascending
                order.
        """

        key_counts: Counter[str] = Counter(key for term in glossary for key in term.keys)

        index: dict[str, list[int]] = {}
        for term_id, term in enumerate(glossary):
            if not term.keys:
                continue

            rarest_key: str = min(term.keys, key=lambda key: key_counts[key])
            index.setdefault(rarest_key, []).append(term_id)

        return index

    @staticmethod
    def __get_candidate_ids(
        text_keys: frozenset[str], term_index: dict[str, list[int]]
    ) -> list[int]:
        """
        Gets the positions of all glossary terms that may occur in a text. As every term
        is indexed by one of its keys, each term whose keys are all contained in the
        text is a candidate. The candidates have to be checked in glossary order, as
        found terms are removed from the text to avoid overlaps with shorter terms.

        Args:
            text_keys (frozenset[str]): The normalized words of the text.
            term_index (dict[str, list[int]]): The term index of the glossary.

        Returns:
            list[int]: The positions of the candidate terms in ascending order.
        """

        candidate_ids: set[int] = set()
        for key in text_keys:
            candidate_ids.update(term_index.get(key, ()))

        return sorted(candidate_ids)

    def get_glossary(
        self, translation_strings: dict[Path, StringList]
    ) -> list[TranslationGlossary.Term]:
        """
        Args:
            translation_strings (dict[Path, StringList]):
                The strings of the currently edited translation.

        Returns:
            list[TranslationGlossary.Term]: A list of all glossary terms.
        """

        glossary: list[TranslationGlossary.Term] = self.__database_glossary.copy()
        glossary += [
            TranslationGlossary.Term(
                original=original,
                translated=translated,
                source=TranslationGlossary.TermSource.Mod,
            )
            for mod_file_strings in translation_strings.values()
            for original, translated in self.__get_names_from_string_list(
                mod_file_strings
            ).items()
        ]
        glossary += [
            TranslationGlossary.Term(
                original=original,
                translated=translated,
                source=TranslationGlossary.TermSource.UserGlossary,
            )
            for original, translated in self.__translator_config.glossary.items()
            if 0 < len(get_words(original)) <= TranslationGlossary.MAX_TERM_WORDS
        ]

        return sorted(
            unique(glossary, key=lambda t: t.original.lower()),
            key=lambda t: len(t.original),
            reverse=True,
        )
