"""
Copyright (c) Cutleast
"""

import os

import qtawesome as qta
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton


class LinkButton(QPushButton):
    """
    Custom QPushButton adapted for hyperlinks.
    """

    def __init__(
        self, url: str, display_text: str | None = None, icon: QIcon | None = None
    ) -> None:
        super().__init__()

        if display_text is not None:
            self.setText(display_text)

        self.setIcon(
            icon
            or qta.icon("fa5s.external-link-alt", color=self.palette().text().color())
        )
        self.clicked.connect(lambda: os.startfile(url))
        self.setToolTip(url)
