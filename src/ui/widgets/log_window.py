"""
Copyright (c) Cutleast
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QPlainTextEdit


class LogWindow(QPlainTextEdit):
    """
    Window for displaying the application log in realtime.
    """

    def __init__(self, initial_text: str = "") -> None:
        super().__init__()

        self.setWindowTitle(self.tr("Log"))
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setObjectName("protocol")
        self.resize(800, 400)

        self.setReadOnly(True)
        self.setPlainText(initial_text.removesuffix("\n"))
        self.moveCursor(QTextCursor.MoveOperation.End)

    def addMessage(self, message: str) -> None:
        """
        Adds a message to the bottom of the log window and scrolls to the bottom.

        Args:
            message (str): The message to add to the log window
        """

        self.appendPlainText(message.removesuffix("\n"))
        self.moveCursor(QTextCursor.MoveOperation.End)
