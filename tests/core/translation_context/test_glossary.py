"""
Copyright (c) Cutleast
"""

import random
import re
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

from core.config.translator_config import TranslatorConfig
from core.database.database import TranslationDatabase
from core.string.types import StringList
from core.translation_context.glossary import TranslationGlossary
from core.utilities.text import find_term, get_words, normalize_word, plain_text


class TestTranslationGlossary:
    """
    Tests `core.translation_context.glossary.TranslationGlossary`.
    """

    VOCABULARY: list[str] = [
        "the",
        "of",
        "dragon",
        "dragons",
        "dragon's",
        "sword",
        "swords",
        "box",
        "boxes",
        "sphere",
        "spheres",
        "dark",
        "brotherhood",
        "s",
        "es",
        "e",
        "elder",
        "scroll",
        "scrolls",
        "whiterun",
        "hold",
        "guard",
    ]
    """Words used for generating terms and texts with many overlaps."""

    @staticmethod
    def __create_glossary(user_glossary: dict[str, str]) -> TranslationGlossary:
        """
        Creates a glossary with an empty database and the specified user glossary.

        Args:
            user_glossary (dict[str, str]): The user-configured glossary.

        Returns:
            TranslationGlossary: The created glossary.
        """

        database = MagicMock(spec=TranslationDatabase)
        database.vanilla_translation.strings = {}
        database.user_translations = []
        config = MagicMock(spec=TranslatorConfig)
        config.glossary = user_glossary

        return TranslationGlossary(config, database)

    @staticmethod
    def __scan_brute_force(
        glossary: list[TranslationGlossary.Term], text: str
    ) -> list[str]:
        """
        Scans a text for glossary terms by checking every term of the glossary. This is
        the reference behavior that the indexed lookup must reproduce.

        Args:
            glossary (list[TranslationGlossary.Term]): The sorted glossary.
            text (str): The text to scan.

        Returns:
            list[str]: The originals of the found terms in the order they were found.
        """

        search_text: str = plain_text(text.lower())
        text_keys: frozenset[str] = frozenset(
            normalize_word(word) for word in get_words(search_text)
        )

        found_terms: list[str] = []
        for term in glossary:
            if not term.keys.issubset(text_keys):
                continue

            match: Optional[re.Match[str]] = find_term(
                search_text, term.original, inflected=False
            )
            if match is not None:
                found_terms.append(term.original)
                search_text = (
                    search_text[: match.start()]
                    + " " * len(match.group())
                    + search_text[match.end() :]
                )
                text_keys = frozenset(
                    normalize_word(word) for word in get_words(search_text)
                )

        return found_terms

    def test_longer_terms_take_precedence_over_overlapping_shorter_terms(self) -> None:
        """
        Tests that a shorter term is not found within an already found longer term, but
        still elsewhere in the text.
        """

        # given
        glossary: TranslationGlossary = TestTranslationGlossary.__create_glossary(
            {
                "Dark Brotherhood": "Dunkle Bruderschaft",
                "Brotherhood": "Bruderschaft",
                "Dragon": "Drache",
                "Elder Scroll": "Schriftrolle der Alten",
            }
        )
        text: str = "The <Alias=Player> joined the Dark Brotherhood to fight dragons."
        translation_strings: dict[Path, StringList] = {}

        # when
        terms: list[TranslationGlossary.Term] = glossary.get_terms_of_string(
            text, translation_strings
        )

        # then
        assert [term.original for term in terms] == ["Dark Brotherhood", "Dragon"]

    def test_indexed_lookup_matches_brute_force_scan(self) -> None:
        """
        Tests that the indexed lookup finds exactly the same terms in the same order as
        checking every term of the glossary.
        """

        # given
        rng = random.Random(42)
        user_glossary: dict[str, str] = {}
        for _ in range(300):
            word_count: int = rng.randint(1, 3)
            original: str = " ".join(
                rng.choice(TestTranslationGlossary.VOCABULARY).capitalize()
                for _ in range(word_count)
            )
            user_glossary[original] = original.upper()

        texts: list[str] = []
        for _ in range(300):
            word_count = rng.randint(1, 12)
            texts.append(
                " ".join(
                    rng.choice(TestTranslationGlossary.VOCABULARY)
                    for _ in range(word_count)
                )
            )
        texts.append("The [Dragon] of <mag> Whiterun Hold, 3 swords & 2 boxes.")

        glossary: TranslationGlossary = TestTranslationGlossary.__create_glossary(
            user_glossary
        )
        translation_strings: dict[Path, StringList] = {}
        sorted_glossary: list[TranslationGlossary.Term] = glossary.get_glossary(
            translation_strings
        )
        expected: list[list[str]] = [
            TestTranslationGlossary.__scan_brute_force(sorted_glossary, text)
            for text in texts
        ]

        # when
        terms: list[list[TranslationGlossary.Term]] = glossary.get_terms_of_strings(
            texts, translation_strings
        )

        # then
        actual: list[list[str]] = [
            [term.original for term in text_terms] for text_terms in terms
        ]
        assert actual == expected
        assert any(expected), "The generated texts should contain glossary terms."
