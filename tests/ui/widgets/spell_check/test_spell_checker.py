"""
Copyright (c) Cutleast
"""

from pathlib import Path

from ui.widgets.spell_check.spell_checker import SpellChecker


class TestSpellChecker:
    """
    Tests `ui.widgets.spell_check.spell_checker.SpellChecker`.
    """

    UNENCODABLE_WORD: str = "„Hallo"
    """
    German word with a leading low quotation mark, which the ISO-8859-1 encoded German
    dictionary cannot represent.
    """

    def test_is_correct_accepts_unencodable_word(self, tmp_path: Path) -> None:
        """
        Tests that words with characters outside the dictionary's encoding are not
        rejected with a `UnicodeEncodeError`.
        """

        # given
        checker = SpellChecker("german", tmp_path)

        # when
        result: bool = checker.is_correct(TestSpellChecker.UNENCODABLE_WORD)

        # then
        assert result

    def test_is_correct_still_checks_encodable_words(self, tmp_path: Path) -> None:
        """
        Tests that encodable words are still checked against the dictionary.
        """

        # given
        checker = SpellChecker("german", tmp_path)

        # then
        assert checker.is_correct("Hallo")
        assert not checker.is_correct("Halloxyzq")

    def test_get_suggestions_for_unencodable_word(self, tmp_path: Path) -> None:
        """
        Tests that no suggestions are returned for words with characters outside the
        dictionary's encoding.
        """

        # given
        checker = SpellChecker("german", tmp_path)

        # when
        suggestions: list[str] = checker.get_suggestions(
            TestSpellChecker.UNENCODABLE_WORD
        )

        # then
        assert suggestions == []

    def test_unencodable_word_is_not_added_to_dictionary(self, tmp_path: Path) -> None:
        """
        Tests that words with characters outside the dictionary's encoding are not
        persisted in the user dictionary.
        """

        # given
        checker = SpellChecker("german", tmp_path)

        # when
        checker.add_word_to_dictionary(TestSpellChecker.UNENCODABLE_WORD)

        # then
        assert not (tmp_path / "hunspell" / "german.dic").exists()
