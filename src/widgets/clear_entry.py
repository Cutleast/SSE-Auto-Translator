"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtWidgets as qtw


class ClearEntry(qtw.QLineEdit):
    """
    Adapted QLineEdit with dedicated clear button.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        hlayout = qtw.QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(hlayout)

        hlayout.addStretch()

        clear_button = qtw.QPushButton()
        clear_button.setCursor(qtc.Qt.CursorShape.ArrowCursor)
        clear_button.setIcon(qta.icon("fa.close", color="#ffffff"))
        clear_button.clicked.connect(lambda: self.setText(""))
        clear_button.clicked.connect(self.setFocus)
        clear_button.hide()
        hlayout.addWidget(clear_button)

        self.textChanged.connect(
            lambda text: clear_button.setVisible(bool(text.strip()))
        )
