"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QCompleter


class CompletionBox(QComboBox):
    """
    Modified QComboBox to search.
    """

    def __init__(self):
        super().__init__()

        self.setEditable(True)

    def addItems(self, texts: Sequence[str]) -> None:
        super().addItems(texts)

        completer = QCompleter(texts)
        completer.popup().setObjectName("completer_popup")
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setCompleter(completer)
