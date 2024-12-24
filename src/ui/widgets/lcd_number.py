"""
Copyright (c) Cutleast
"""

from typing import Optional

from PySide6.QtWidgets import QLCDNumber, QWidget


class LCDNumber(QLCDNumber):
    """
    Adapted QLCDNumber with a fixed height.

    This is required because QLCDNumber cannot be styled with QSS.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.setFixedHeight(40)
