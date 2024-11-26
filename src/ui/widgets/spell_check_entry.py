"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import string
from typing import Iterator

import spylls.hunspell as hunspell
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction, QCursor, QTextCharFormat
from PySide6.QtWidgets import QApplication, QPlainTextEdit


class SpellCheckEntry(QPlainTextEdit):
    """
    Adapted QPlainTextEdit with spell check feature.

    Given `language` must be one of the languages in `utilities.constants.SUPPORTED_LANGS`!
    """

    log = logging.getLogger("SpellCheckEntry")

    def __init__(self, *args, language: str, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            self.checker = hunspell.Dictionary.from_files("./data/hunspell/" + language)
            self.log.info("Loaded Hunspell dictionary.")
        except FileNotFoundError:
            self.log.error(
                f"Failed to load dictionary for specified language {language!r}: Dictionary not found!"
            )
            self.log.warning("Spell checking not available!")
            self.checker = None

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)

        self.textChanged.connect(self.on_text_edit)

    def on_context_menu(self, point: QPoint):
        mouse_pos = self.mapFromGlobal(QCursor.pos())
        mouse_pos.setY(mouse_pos.y() - 9)
        text_cursor = self.cursorForPosition(mouse_pos)
        text_cursor.movePosition(
            text_cursor.MoveOperation.WordLeft, text_cursor.MoveMode.MoveAnchor
        )
        text_cursor.select(text_cursor.SelectionType.WordUnderCursor)

        word = text_cursor.selectedText()
        fmt = text_cursor.charFormat()

        def ignore():
            # TODO: Reimplement
            raise NotImplementedError
            # self.checker.add(word)
            self.on_text_edit()
            self.log.debug(f"Ignored {word!r}.")

        menu = self.createStandardContextMenu()

        if (
            fmt.underlineStyle() == fmt.UnderlineStyle.WaveUnderline
            and self.checker is not None
        ):
            first_std_action = menu.actions()[0]
            suggestions: Iterator[str] = self.checker.suggest(word)

            if suggestions is not None:
                separator = menu.insertSeparator(first_std_action)

                def get_func(sug):
                    def func():
                        text_cursor.insertText(sug)
                        self.setTextCursor(text_cursor)

                    return func

                for suggestion in suggestions:
                    action = QAction(suggestion)
                    action.triggered.connect(get_func(suggestion))
                    menu.insertAction(separator, action)

                separator = menu.insertSeparator(first_std_action)

                ignore_action = QAction("Ignore")
                ignore_action.triggered.connect(ignore)
                # menu.insertAction(separator, ignore_action)

        menu.exec(self.mapToGlobal(point))

    def on_text_edit(self):
        text = self.toPlainText()

        if text[-1:] in string.punctuation + string.whitespace:
            try:
                self.textChanged.disconnect(self.on_text_edit)
            except RuntimeError:
                pass
            self.spell_check()
            self.textChanged.connect(self.on_text_edit)

    def spell_check(self):
        if self.checker is None:
            return

        cursor = self.textCursor()
        cursor.setPosition(0)

        text = self.toPlainText()

        for word in text.split():
            word = word.strip(string.punctuation + string.whitespace)

            pos = text.find(word, cursor.position())

            if pos != -1:
                cursor.setPosition(pos)
            else:
                continue

            cursor.select(cursor.SelectionType.WordUnderCursor)

            word_correct = self.checker.lookup(word)

            fmt = QTextCharFormat()

            if word_correct:
                fmt.setUnderlineStyle(fmt.UnderlineStyle.NoUnderline)
            else:
                fmt.setUnderlineColor(Qt.GlobalColor.red)
                fmt.setUnderlineStyle(fmt.UnderlineStyle.WaveUnderline)

            cursor.setCharFormat(fmt)


if __name__ == "__main__":
    app = QApplication()

    widget = SpellCheckEntry(language="german")
    widget.show()

    app.exec()
