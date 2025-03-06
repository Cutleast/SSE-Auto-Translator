"""
Copyright (c) Cutleast
"""

from typing import Optional

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.database.string import String


class EditorHelpDialog(QDialog):
    """
    Dialog for showing help about the string states.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.setModal(True)
        self.setWindowTitle(self.tr("Help"))

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        help_label = QLabel(
            self.tr("Below is an overview of the various states a string can have:")
        )
        help_label.setObjectName("relevant_label")
        help_label.setWordWrap(True)
        vlayout.addWidget(help_label)

        vlayout.addSpacing(25)

        flayout = QFormLayout()
        flayout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        vlayout.addLayout(flayout)

        for status in String.Status:
            color: Optional[QColor] = String.Status.get_color(status)

            if color is None:
                label = QLabel(status.get_localized_name())
                flayout.addRow(label)
            else:
                color_name: str = color.name()

                color_label = QLabel()
                color_label.setPixmap(
                    qta.icon("mdi6.square-rounded", color=color_name).pixmap(32, 32)
                )
                flayout.addRow(status.get_localized_name(), color_label)

        vlayout.addSpacing(25)

        ok_button = QPushButton(self.tr("Ok"))
        ok_button.clicked.connect(self.accept)
        vlayout.addWidget(ok_button)
