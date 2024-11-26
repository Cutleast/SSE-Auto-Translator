"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Callable

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QWidget


class Thread(QThread):
    """
    Inherited by QThread and designed for easier usage.
    """

    def __init__(self, target: Callable, name: str = None, parent: QWidget = None):
        super().__init__(parent)

        self.target = target

        if name is not None:
            self.setObjectName(name)

    def run(self):
        self.target()
