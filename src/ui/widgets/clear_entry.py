"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Any

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton


class ClearEntry(QLineEdit):
    """
    Adapted QLineEdit with dedicated clear button.
    """

    def __init__(self, *args: Any, **kwargs: dict[str, Any]):
        super().__init__(*args, **kwargs)

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(hlayout)

        hlayout.addStretch()

        clear_button = QPushButton()
        clear_button.setCursor(Qt.CursorShape.ArrowCursor)
        clear_button.setIcon(qta.icon("fa.close", color="#ffffff"))
        clear_button.clicked.connect(lambda: self.setText(""))
        clear_button.clicked.connect(self.setFocus)
        clear_button.hide()
        hlayout.addWidget(clear_button)

        self.textChanged.connect(
            lambda text: clear_button.setVisible(bool(text.strip()))
        )
