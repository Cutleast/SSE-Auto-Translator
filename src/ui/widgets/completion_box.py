"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Optional, Sequence, override

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QComboBox, QCompleter


class CompletionBox(QComboBox):
    """
    Modified QComboBox to search.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setEditable(True)

    @override
    def addItems(self, texts: Sequence[str]) -> None:
        super().addItems(texts)

        completer = QCompleter(texts)
        popup: Optional[QAbstractItemView] = completer.popup()
        if popup:
            popup.setObjectName("completer_popup")
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setCompleter(completer)
