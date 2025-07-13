"""
Copyright (c) Cutleast
"""

import string
from typing import Optional

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction, QCursor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QMenu, QPlainTextEdit, QWidget

from ui.utilities import apply_shadow

from .spell_checker import SpellChecker


class SpellCheckEdit(QPlainTextEdit):
    """
    A QPlainTextEdit with an integrated spell checker.
    """

    CURSOR_Y_OFFSET = 9
    """Y-offset to adjust for mouse click hotspot."""

    __checker: SpellChecker

    def __init__(
        self, language: str, initial_text: str = "", parent: Optional[QWidget] = None
    ) -> None:
        """
        Args:
            language (str):
                The lowered name of the language to load the spell checker for.
            initial_text (str, optional): Initial text to insert. Defaults to "".
            parent (Optional[QWidget], optional): Parent widget. Defaults to None.
        """

        super().__init__(parent)

        self.__checker = SpellChecker(language)

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
        word, cursor = self.__get_word_under_cursor()

        if (
            cursor.charFormat().underlineStyle()
            == QTextCharFormat.UnderlineStyle.WaveUnderline
        ):
            for sug in self.__checker.get_suggestions(word):
                action = QAction(sug)
                action.triggered.connect(
                    lambda _, s=sug: self.__replace_word(cursor, s)
                )
                menu.insertAction(menu.actions()[0], action)

            menu.insertSeparator(menu.actions()[0])

        menu.exec(self.mapToGlobal(point))

    def __on_text_changed(self) -> None:
        text: str = self.toPlainText()

        if not text or text[-1:] not in string.punctuation + string.whitespace:
            return

        # disconnect to prevent the underlining of wrong words from retriggering this
        # function
        try:
            self.textChanged.disconnect(self.__on_text_changed)
        except RuntimeError:
            pass

        self.__apply_spell_check()
        self.textChanged.connect(self.__on_text_changed)

    def __apply_spell_check(self) -> None:
        cursor: QTextCursor = self.textCursor()
        cursor.setPosition(0)

        text: str = self.toPlainText()

        for word in text.split():
            stripped: str = word.strip(string.punctuation + string.whitespace)
            pos: int = text.find(stripped, cursor.position())

            if pos == -1:
                continue

            cursor.setPosition(pos)
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)

            fmt = QTextCharFormat()
            if not self.__checker.is_correct(stripped):
                fmt.setUnderlineColor(Qt.GlobalColor.red)
                fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)

            cursor.setCharFormat(fmt)

    def __get_word_under_cursor(self) -> tuple[str, QTextCursor]:
        mouse_pos: QPoint = self.mapFromGlobal(QCursor.pos())
        mouse_pos.setY(mouse_pos.y() - SpellCheckEdit.CURSOR_Y_OFFSET)

        cursor: QTextCursor = self.cursorForPosition(mouse_pos)
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)

        return cursor.selectedText(), cursor

    def __replace_word(self, cursor: QTextCursor, suggestion: str) -> None:
        cursor.insertText(suggestion)
        self.setTextCursor(cursor)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication()
    editor = SpellCheckEdit(language="german")
    editor.show()
    app.exec()
