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
