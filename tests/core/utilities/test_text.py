"""
Copyright (c) Cutleast
"""

import pytest

from core.utilities.game_language import GameLanguage
from core.utilities.text import (
    find_term,
    find_term_stems,
    fold_word,
    get_word_stems,
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
