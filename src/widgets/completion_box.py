"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Sequence
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw


class CompletionBox(qtw.QComboBox):
    """
    Modified QComboBox to search.
    """

    def __init__(self):
        super().__init__()

        self.setEditable(True)
    
    def addItems(self, texts: Sequence[str]) -> None:
        super().addItems(texts)

        completer = qtw.QCompleter(texts)
        completer.popup().setObjectName("completer_popup")
        completer.setCaseSensitivity(qtc.Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(qtw.QCompleter.CompletionMode.PopupCompletion)
        self.setCompleter(completer)
