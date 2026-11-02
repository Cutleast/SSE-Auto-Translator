"""
Copyright (c) Cutleast
"""

from pathlib import Path

from PySide6.QtGui import QTextCharFormat, QTextCursor
from pytestqt.qtbot import QtBot

from ui.widgets.spell_check.spell_check_edit import SpellCheckEdit


class TestSpellCheckEdit:
    """
    Tests `ui.widgets.spell_check.spell_check_edit.SpellCheckEdit`.
    """

    def test_typographic_quotes_do_not_break_spell_check(
        self, tmp_path: Path, qtbot: QtBot
    ) -> None:
        """
        Tests that text with typographic quotation marks is spell checked without
        errors and that the quoted word itself is checked.
        """

        # given
        widget = SpellCheckEdit(language="german", user_data_path=tmp_path)
        qtbot.addWidget(widget)

        # when
        widget.setPlainText("Er sagte „Halloxyzq“ ")

        # then
        cursor: QTextCursor = widget.textCursor()
        cursor.setPosition(widget.toPlainText().index("Halloxyzq") + 1)
        assert (
            cursor.charFormat().underlineStyle()
            == QTextCharFormat.UnderlineStyle.WaveUnderline
        )

    def test_touching_quoted_words_are_checked_separately(
        self, tmp_path: Path, qtbot: QtBot
    ) -> None:
        """
        Tests that quoted words without whitespace between them are checked one by one,
        so that a misspelled word is underlined and a correct one is not.
        """

        # given
        widget = SpellCheckEdit(language="german", user_data_path=tmp_path)
        qtbot.addWidget(widget)

        # when
        widget.setPlainText("„Halloxyzq“,„Hallo“ ")

        # then
        text: str = widget.toPlainText()
        cursor: QTextCursor = widget.textCursor()
        cursor.setPosition(text.index("Halloxyzq") + 1)
        assert (
            cursor.charFormat().underlineStyle()
            == QTextCharFormat.UnderlineStyle.WaveUnderline
        )
        cursor.setPosition(text.index("„Hallo“") + 2)
        assert (
            cursor.charFormat().underlineStyle()
            != QTextCharFormat.UnderlineStyle.WaveUnderline
        )

    def test_word_pattern_keeps_apostrophes_and_hyphens(self) -> None:
        """
        Tests that words are split at punctuation, except apostrophes and hyphens
        inside a word.
        """

        # when
        words: list[str] = SpellCheckEdit.WORD_PATTERN.findall(
            "„Wort“,„Zwei“ don't geht’s E-Mail -frei- 3,5"
        )

        # then
        assert words == [
            "Wort",
            "Zwei",
            "don't",
            "geht’s",
            "E-Mail",
            "frei",
            "3",
            "5",
        ]
