"""
Copyright (c) Cutleast
"""

from pathlib import Path

from core.utilities.spell_checker import SpellChecker
from tests.base_test import BaseTest
from tests.setup.paths import DICTIONARY_PATH


class TestSpellChecker(BaseTest):
    """
    Tests `core.utilities.spell_checker.SpellChecker`.
    """

    def test_checks_words_with_language_dictionary(self) -> None:
        """
        Tests that words are checked against the dictionary of the language.
        """

        # given
        spell_checker = SpellChecker("german", None, DICTIONARY_PATH)

        # when
        correct: bool = spell_checker.is_correct("Schwert")
        misspelled: bool = spell_checker.is_correct("Schwrt")
        suggestions: list[str] = spell_checker.get_suggestions("Schwrt")

        # then
        assert correct
        assert not misspelled
        assert "Schwert" in suggestions

    def test_accepts_all_words_without_dictionary_folder(self) -> None:
        """
        Tests that spell checking is disabled if no dictionary folder is specified for
        a language.
        """

        # given
        spell_checker = SpellChecker("german", None)

        # when / then
        assert spell_checker.is_correct("Schwrt")
        assert spell_checker.get_suggestions("Schwrt") == []

    def test_accepts_all_words_with_missing_dictionary(self, tmp_path: Path) -> None:
        """
        Tests that spell checking is disabled if the dictionary of the language does
        not exist in the dictionary folder.
        """

        # given
        spell_checker = SpellChecker("german", None, tmp_path)

        # when / then
        assert spell_checker.is_correct("Schwrt")
