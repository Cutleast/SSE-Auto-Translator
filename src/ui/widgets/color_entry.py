"""
Copyright (c) Cutleast
"""

from typing import Any, override

import qtawesome as qta
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QHBoxLayout, QLineEdit, QPushButton


class ColorLineEdit(QLineEdit):
    """
    Custom QLineEdit with a "Choose color" button to open a QColorDialog.
    """

    __preset_colors: list[str] = []
    __choose_color_button: QPushButton

    def __init__(
        self, preset_colors: list[str], *args: Any, **kwargs: dict[str, Any]
    ) -> None:
        super().__init__(*args, **kwargs)

        self.__preset_colors = preset_colors

        hlayout: QHBoxLayout = QHBoxLayout(self)
        hlayout.setContentsMargins(0, 0, 0, 0)

        # Push Choose Color Button to the right-hand side
        hlayout.addStretch()

        self.__choose_color_button = QPushButton()
        self.__choose_color_button.setIconSize(QSize(24, 24))
        self.__choose_color_button.setIcon(
            qta.icon("mdi6.square-rounded", color=self.palette().text().color())
        )
        self.__choose_color_button.clicked.connect(self.__choose_color)
        self.__choose_color_button.setCursor(Qt.CursorShape.ArrowCursor)
        hlayout.addWidget(self.__choose_color_button)

    @override
    def setText(self, text: str) -> None:  # type: ignore
        super().setText(text)

        self.__choose_color_button.setIcon(
            qta.icon("mdi6.square-rounded", color=self.text())
        )

    def __choose_color(self) -> None:
        colordialog = QColorDialog()
        colordialog.setOption(
            colordialog.ColorDialogOption.DontUseNativeDialog, on=True
        )
        for i, color in enumerate(self.__preset_colors):
            colordialog.setCustomColor(i, QColor(color))
        color = self.text()
        if QColor.isValidColor(color):
            colordialog.setCurrentColor(QColor(color))
        if colordialog.exec():
            self.setText(colordialog.currentColor().name(QColor.NameFormat.HexRgb))
