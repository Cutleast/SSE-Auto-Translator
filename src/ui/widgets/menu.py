"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Optional, override

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QMenu, QWidget

from ..utilities import apply_shadow


class Menu(QMenu):
    """
    Adapted QMenu with a custom drop shadow.
    """

    def __init__(
        self,
        icon: Optional[QIcon | QPixmap] = None,
        title: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ):
        if title is not None:
            super().__init__(title, parent)
        else:
            super().__init__(parent)

        if icon is not None:
            self.setIcon(icon)

        self.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
        self.aboutToShow.connect(self.show)

    @override
    def show(self) -> None:
        super().show()

        apply_shadow(self, size=4, shadow_color="#181818")
