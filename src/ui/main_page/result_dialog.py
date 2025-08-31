"""
Copyright (c) Cutleast
"""

from typing import Optional

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

from core.mod_file.translation_status import TranslationStatus


class ResultDialog(QDialog):
    """
    Dialog for showing a summary of the scan results.
    """

    def __init__(
        self, summary: dict[TranslationStatus, int], parent: Optional[QWidget]
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Scan Result"))

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        vlayout.addSpacing(15)

        title_label = QLabel(self.tr("Scan Result"))
        title_label.setObjectName("h1")
        vlayout.addWidget(title_label)

        vlayout.addSpacing(15)

        flayout = QFormLayout()
        flayout.setHorizontalSpacing(50)
        flayout.setFormAlignment(Qt.AlignmentFlag.AlignRight)
        vlayout.addLayout(flayout)

        for status, count in summary.items():
            color: Optional[QColor] = TranslationStatus.get_color(status)

            if color is None:
                label = QLabel(status.get_localized_name())
                count_label = QLabel(str(count))
                flayout.addRow(label, count_label)
            else:
                color_name: str = color.name()
                label = QLabel(
                    f'<font color="{color_name}">{status.get_localized_name()}:</font>'
                )
                count_label = QLabel(f'<font color="{color_name}">{count}</font>')
                flayout.addRow(label, count_label)

        vlayout.addSpacing(15)

        ok_button = QPushButton(self.tr("Ok"))
        ok_button.clicked.connect(self.accept)
        vlayout.addWidget(ok_button)
