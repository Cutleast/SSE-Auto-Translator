"""
Copyright (c) Cutleast
"""

import re
import string
import unicodedata
from pathlib import Path
from typing import Optional

from cutleast_core_lib.ui.utilities import apply_shadow
from PySide6.QtCore import QPoint, QSignalBlocker, Qt
from PySide6.QtGui import QAction, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QMenu, QPlainTextEdit, QWidget

from ui.utilities.icon_provider import IconProvider

from .spell_checker import SpellChecker


class SpellCheckEdit(QPlainTextEdit):
    """
    A QPlainTextEdit with an integrated spell checker.
    """

    CURSOR_Y_OFFSET = 9
    """Y-offset to adjust for mouse click hotspot."""

    WORD_PATTERN: re.Pattern[str] = re.compile(r"\w+(?:['’-]\w+)*")
    """
    Matches a single word to spell check. Any punctuation separates words, except
    apostrophes and hyphens between letters, so that "„Wort“,„Zwei“" yields two
    words while "don't" and "E-Mail" stay whole.
    """

    __checker: SpellChecker

    def __init__(
        self,
        language: str,
        user_data_path: Path,
        initial_text: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Args:
            language (str):
                The lowered name of the language to load the spell checker for.
            user_data_path (Path): Path to the user data directory.
            initial_text (str, optional): Initial text to insert. Defaults to "".
            parent (Optional[QWidget], optional): Parent widget. Defaults to None.
        """

        super().__init__(parent)

        self.__checker = SpellChecker(language, user_data_path)

        self.setPlainText(initial_text)
        self.textChanged.connect(self.__on_text_changed)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__on_context_menu)

    def __on_context_menu(self, point: QPoint) -> None:
        menu: QMenu = self.createStandardContextMenu()
        menu.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
        apply_shadow(menu, size=4, shadow_color="#181818")

        word: str
        cursor: QTextCursor
        word, cursor = self.__get_word_at_point(point)

        if (
            cursor.charFormat().underlineStyle()
            == QTextCharFormat.UnderlineStyle.WaveUnderline
        ):
            menu.insertSeparator(menu.actions()[0])

            add_action = QAction(self.tr("Add to dictionary"))
            add_action.setIcon(IconProvider.get_qta_icon("mdi6.book-plus"))
            add_action.triggered.connect(lambda: self.__add_word_to_dictionary(word))
            menu.insertAction(menu.actions()[0], add_action)

            menu.insertSeparator(menu.actions()[0])

            for sug in reversed(self.__checker.get_suggestions(word)):
                action = QAction(sug)
                action.triggered.connect(lambda _, s=sug: self.__replace_word(cursor, s))
                menu.insertAction(menu.actions()[0], action)

        menu.exec(self.mapToGlobal(point))

    def __on_text_changed(self) -> None:
        text: str = self.toPlainText()

        if not text or not SpellCheckEdit.__is_separator(text[-1]):
            return

        # block textChanged signal to avoid recursion
        with QSignalBlocker(self):
            self.__apply_spell_check()

    def __apply_spell_check(self) -> None:
        """
        Underlines every misspelled word and removes outdated underlines.
        """

        cursor: QTextCursor = self.textCursor()

        # Reset all formats first, so that separators never keep an old underline.
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.setCharFormat(QTextCharFormat())

        error_format = QTextCharFormat()
        error_format.setUnderlineColor(Qt.GlobalColor.red)
        error_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)

        for match in SpellCheckEdit.WORD_PATTERN.finditer(self.toPlainText()):
            if self.__checker.is_correct(match.group()):
                continue

            cursor.setPosition(match.start())
            cursor.setPosition(match.end(), QTextCursor.MoveMode.KeepAnchor)
            cursor.setCharFormat(error_format)

    def __get_word_at_point(self, point: QPoint) -> tuple[str, QTextCursor]:
        """
        Gets the word at a widget position, using the same word boundaries as the
        spell check.

        Args:
            point (QPoint): Position in widget coordinates.

        Returns:
            tuple[str, QTextCursor]: The word and a cursor selecting it.
        """

        cursor: QTextCursor = self.cursorForPosition(point)
        position: int = cursor.position()

        for match in SpellCheckEdit.WORD_PATTERN.finditer(self.toPlainText()):
            if match.start() <= position <= match.end():
                cursor.setPosition(match.start())
                cursor.setPosition(match.end(), QTextCursor.MoveMode.KeepAnchor)
                return match.group(), cursor

        cursor.select(QTextCursor.SelectionType.WordUnderCursor)

        return cursor.selectedText(), cursor

    def __replace_word(self, cursor: QTextCursor, suggestion: str) -> None:
        cursor.insertText(suggestion)
        self.setTextCursor(cursor)

    @staticmethod
    def __is_separator(char: str) -> bool:
        """
        Checks whether a character separates words for spell checking.

        Besides ASCII punctuation and whitespace, this includes all Unicode
        punctuation, for example typographic quotes like '„', '“' and '»'.

        Args:
            char (str): Single character to check.

        Returns:
            bool: Whether the character is punctuation or whitespace.
        """

        return (
            char in string.punctuation
            or char.isspace()
            or unicodedata.category(char).startswith("P")
        )

    def __add_word_to_dictionary(self, word: str) -> None:
        self.__checker.add_word_to_dictionary(word)

        # block textChanged signal to avoid recursion
        with QSignalBlocker(self):
            self.__apply_spell_check()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication()
    editor = SpellCheckEdit(language="german", user_data_path=Path("user_data"))
    editor.show()
    app.exec()
