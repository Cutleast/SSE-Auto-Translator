"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton


class SearchBar(QLineEdit):
    """
    Adapted QLineEdit with search icon, clear button and case sensitivity toggle.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.addAction(
            qta.icon("fa.search", color="#ffffff"),
            QLineEdit.ActionPosition.LeadingPosition,
        )

        hlayout = QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(hlayout)

        hlayout.addStretch()

        self.cs_toggle = QPushButton()
        self.cs_toggle.setCursor(Qt.CursorShape.ArrowCursor)
        self.cs_toggle.setIcon(
            qta.icon("mdi6.format-letter-case", color="#ffffff", scale_factor=1.5)
        )
        self.cs_toggle.setCheckable(True)
        self.cs_toggle.clicked.connect(self.setFocus)
        self.cs_toggle.clicked.connect(lambda: self.textChanged.emit(self.text()))
        self.cs_toggle.hide()
        hlayout.addWidget(self.cs_toggle)

        clear_button = QPushButton()
        clear_button.setCursor(Qt.CursorShape.ArrowCursor)
        clear_button.setIcon(qta.icon("fa.close", color="#ffffff"))
        clear_button.clicked.connect(lambda: self.setText(""))
        clear_button.clicked.connect(self.setFocus)
        clear_button.clicked.connect(self.returnPressed.emit)
        clear_button.hide()
        hlayout.addWidget(clear_button)

        self.textChanged.connect(
            lambda text: (
                clear_button.setVisible(bool(text.strip())),
                self.cs_toggle.setVisible(bool(text.strip())),
            )
        )
