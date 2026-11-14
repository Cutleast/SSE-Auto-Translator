"""
Copyright (c) Cutleast
"""

import re
from typing import Optional

import pytest

from core.utilities.game_language import GameLanguage
from core.utilities.text import (
    Occurrences,
    find_all_terms,
    find_term,
    find_term_stems,
    fold_word,
    get_placeholders,
    get_word_stems,
    get_words,
    is_at_sentence_start,
    normalize_word,
    plain_text,
    remove_non_text,
    stem_word,
)


class TestText:
    """
    Tests `core.utilities.text`.
    """

    TEST_FIND_TERM_WITHOUT_WORD_BOUNDARIES_DATA: list[tuple[str, str]] = [
        ("你就是传说中的龙裔。", "龙裔"),
        ("你是龙裔。", "龙裔"),
        ("伝説のドラゴンボーンが来た", "ドラゴンボーン"),
    ]

    @pytest.mark.parametrize("text, term", TEST_FIND_TERM_WITHOUT_WORD_BOUNDARIES_DATA)
    def test_find_term_without_word_boundaries(self, text: str, term: str) -> None:
        """
        Tests that terms are found within the text of languages without spaces between
        words.
        """

        # when
        with_boundaries: bool = find_term(text, term) is not None
        without_boundaries: bool = (
            find_term(text, term, word_boundaries=False) is not None
        )

        # then
        assert not with_boundaries
        assert without_boundaries

    TEST_FOLD_WORD_DATA: list[tuple[str, str]] = [
        ("Stäbe", "stabe"),
        ("Weißlauf", "weisslauf"),
        ("Âme", "ame"),
        ("형제단", "형제단"),
        ("Йорлунд", "йорлунд"),
        ("Ёлка", "ёлка"),
        ("ガルドール", "ガルドール"),
        ("Ἄλφα", "ἄλφα"),
    ]

    @pytest.mark.parametrize("word, expected_output", TEST_FOLD_WORD_DATA)
    def test_fold_word(self, word: str, expected_output: str) -> None:
        """
        Tests that words are folded case- and accent-insensitively.
        """

        # when
        output: str = fold_word(word)

        # then
        assert output == expected_output

    TEST_FIND_TERM_STEMS_DATA: list[tuple[str, str, GameLanguage, bool]] = [
        ("Ein Riesenseelenstein liegt hier.", "Seelenstein", GameLanguage.German, True),
        ("Zwei Zauberstäbe.", "Stab", GameLanguage.German, True),
        ("Die Daedrafürsten zürnen.", "Daedrafürst", GameLanguage.German, True),
        ("Die Männer kommen.", "Mann", GameLanguage.German, True),
        ("Die Jarlsfrau spricht.", "Jarl", GameLanguage.German, True),
        ("Der Stein liegt da.", "Seelenstein", GameLanguage.German, False),
        ("Les pierres d'âmes", "pierre d'âme", GameLanguage.French, True),
        ("Las gemas de almas", "gema de alma", GameLanguage.Spanish, True),
        ("암흑형제단에 가입", "형제단", GameLanguage.Korean, True),
        ("어둠의 길드", "형제단", GameLanguage.Korean, False),
    ]

    @pytest.mark.parametrize(
        "text, term, language, expected_output", TEST_FIND_TERM_STEMS_DATA
    )
    def test_find_term_stems(
        self, text: str, term: str, language: GameLanguage, expected_output: bool
    ) -> None:
        """
        Tests that terms are found loosely within compounds and with changed stems.
        """

        # when
        output: bool = find_term_stems(
            text, term, language.stemmer_algorithm, language.min_stem_length
        )

        # then
        assert output == expected_output

    TEST_GET_WORD_STEMS_DATA: list[tuple[str, str, GameLanguage, bool]] = [
        ("Vaerminas", "Vaermina", GameLanguage.German, True),
        ("Ulfrics", "Ulfric", GameLanguage.German, True),
        ("Sheogoraths", "Sheogorath", GameLanguage.German, True),
        ("Jarls", "Jarl", GameLanguage.Spanish, True),
        ("Ulfrics", "Ulfric", GameLanguage.Portuguese, True),
        ("Daedras", "Daedra", GameLanguage.Italian, True),
        ("Vaerminas", "Vaermina", GameLanguage.French, True),
        ("Vaerminax", "Vaermina", GameLanguage.German, False),
        ("Vaerminas", "Vaermina", GameLanguage.Turkish, False),
    ]

    @pytest.mark.parametrize(
        "word, known_word, language, expected_output", TEST_GET_WORD_STEMS_DATA
    )
    def test_get_word_stems(
        self, word: str, known_word: str, language: GameLanguage, expected_output: bool
    ) -> None:
        """
        Tests that the stems of a word include the stem of a known word, if the word
        only differs from it by an inflection or a loose suffix of the language.
        """

        # given
        known_stem: str = stem_word(known_word, language.stemmer_algorithm)

        # when
        stems: list[str] = get_word_stems(
            word, language.stemmer_algorithm, language.loose_suffixes
        )

        # then
        assert (known_stem in stems) == expected_output

    @pytest.mark.parametrize(
        "text, expected_output",
        [
            ("Deals <mag> damage.", "Deals   damage."),
            ("[pagebreak]Page {0}", " Page  "),
            ("No markup", "No markup"),
        ],
    )
    def test_plain_text(self, text: str, expected_output: str) -> None:
        """
        Tests that markup and placeholders are replaced with whitespace.

        Args:
            text (str): The input text.
            expected_output (str): The expected plain text.
        """

        # when
        actual_output: str = plain_text(text)

        # then
        assert actual_output == expected_output

    @pytest.mark.parametrize(
        "text, expected_output",
        [
            ("Deals <mag> points of damage!", "Deals points of damage"),
            ("'Tis the dragon's hoard, 100 gold.", "Tis the dragon's hoard gold"),
            pytest.param(
                "Face Cover - Full",
                "Face Cover Full",
                marks=pytest.mark.xfail(
                    strict=True,
                    reason="Hyphens that are not within a word are not removed.",
                ),
            ),
            ("Iron-bound chest", "Iron-bound chest"),
        ],
    )
    def test_remove_non_text(self, text: str, expected_output: str) -> None:
        """
        Tests that only words (including inner apostrophes and hyphens) remain.

        Args:
            text (str): The input text.
            expected_output (str): The expected text.
        """

        # when
        actual_output: str = remove_non_text(text)

        # then
        assert actual_output == expected_output

    @pytest.mark.parametrize(
        "word, expected_output",
        [("Spheres", "spher"), ("Sphere", "spher"), ("Boxes", "box"), ("Box", "box")],
    )
    def test_normalize_word(self, word: str, expected_output: str) -> None:
        """
        Tests that singular and plural forms are normalized to the same word.

        Args:
            word (str): The input word.
            expected_output (str): The expected normalized word.
        """

        # when
        actual_output: str = normalize_word(word)

        # then
        assert actual_output == expected_output

    def test_get_words(self) -> None:
        """
        Tests that only natural-language words are returned.
        """

        # when
        words: list[str] = get_words("Weißlauf's 2nd gate_keeper, <Alias=Player>!")

        # then
        assert words == ["Weißlauf", "s", "nd", "gate", "keeper", "Alias", "Player"]

    @pytest.mark.parametrize(
        "text, term, inflected, expected_match",
        [
            (
                "Die Dunklen Bruderschaft",
                "Dunkle Bruderschaft",
                True,
                "Dunklen Bruderschaft",
            ),
            ("Weißlaufs Tore", "Weißlauf", True, "Weißlaufs"),
            ("Weißlaufs Tore", "Weißlauf", False, "Weißlaufs"),
            ("Weißlaufer Tore", "Weißlauf", False, None),
            # markup is ignored, the match refers to the plain text
            (
                "The <b>Jarl</b> of Whiterun",
                "Jarl of Whiterun",
                True,
                "Jarl  of Whiterun",
            ),
            ("The Jarl of Whiterun", "Jarl of Whiterun", True, "Jarl of Whiterun"),
            ("Nothing here", "Whiterun", True, None),
            ("Anything", "123", True, None),
        ],
    )
    def test_find_term(
        self,
        text: str,
        term: str,
        inflected: bool,
        expected_match: Optional[str],
    ) -> None:
        """
        Tests that terms are found case-insensitively with optional inflection
        suffixes.

        Args:
            text (str): The text to search.
            term (str): The term to search for.
            inflected (bool): Whether to consider inflection suffixes.
            expected_match (Optional[str]): The expected matched text.
        """

        # when
        match: Optional[re.Match[str]] = find_term(text, term, inflected=inflected)

        # then
        assert (match.group() if match is not None else None) == expected_match

    def test_find_all_terms(self) -> None:
        """
        Tests that all occurrences of a term are found.
        """

        # when
        matches: list[re.Match[str]] = find_all_terms(
            "Whiterun guards protect Whiterun's gates.", "Whiterun"
        )

        # then
        assert [match.group() for match in matches] == ["Whiterun", "Whiterun"]

    @pytest.mark.parametrize(
        "text, term, expected_output",
        [
            ("Hold the line!", "Hold", True),
            ('He said: "Hold the line!"', "Hold", True),
            ("Rule the Hold.", "Hold", False),
            ("First line\n- Hold on", "Hold", True),
        ],
    )
    def test_is_at_sentence_start(
        self, text: str, term: str, expected_output: bool
    ) -> None:
        """
        Tests the detection of matches at the start of a sentence.

        Args:
            text (str): The searched text.
            term (str): The term to search for.
            expected_output (bool): Whether the match is at a sentence start.
        """

        # given
        match: Optional[re.Match[str]] = find_term(text, term)
        assert match is not None

        # when
        actual_output: bool = is_at_sentence_start(text, match)

        # then
        assert actual_output == expected_output

    def test_get_placeholders(self) -> None:
        """
        Tests that all supported placeholder kinds are counted.
        """

        # when
        placeholders: Occurrences = get_placeholders(
            "<mag> for <dur>s, <mag> again [pagebreak] {0} {} %d %.2f %s"
        )

        # then
        assert placeholders == {
            "<mag>": 2,
            "<dur>": 1,
            "[pagebreak]": 1,
            "{0}": 1,
            "{}": 1,
            "%d": 1,
            "%.2f": 1,
            "%s": 1,
        }
