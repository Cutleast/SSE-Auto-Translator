"""
Copyright (c) Cutleast
"""

from enum import Enum
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ExportDialog(QDialog):
    """
    Dialog for asking the user for the format the current translation should be exported
    with.
    """

    class ExportFormat(Enum):
        """
        Enum for supported export formats.
        """

        DSD = "DSD"
        """
        The user gets asked for a destination folder where 
        the folder structure and JSON files for the DSD get generated.
        """

        ESP = "ESP"
        """
        The user gets asked for a destination folder where
        the installed plugin files with the translation applied get outputted.
        """

    __value: Optional[ExportFormat] = None

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.setModal(True)
        self.setWindowTitle(self.tr("Export Translation"))

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        vlayout.addSpacing(15)

        text_label = QLabel(
            self.tr("Select the format the translation should be exported with:")
        )
        vlayout.addWidget(text_label)

        vlayout.addSpacing(15)

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        dsd_button = QPushButton(self.tr("DSD Files"))
        dsd_button.clicked.connect(
            lambda: self.__exit_with_value(ExportDialog.ExportFormat.DSD)
        )
        hlayout.addWidget(dsd_button)

        esp_button = QPushButton(self.tr("Plugin Files") + self.tr(" [Experimental]"))
        esp_button.clicked.connect(
            lambda: self.__exit_with_value(ExportDialog.ExportFormat.ESP)
        )
        hlayout.addWidget(esp_button)

        cancel_button = QPushButton(self.tr("Cancel"))
        cancel_button.clicked.connect(self.reject)
        hlayout.addWidget(cancel_button)

    def __exit_with_value(self, value: ExportFormat) -> None:
        self.__value = value
        self.accept()

    def get_value(self) -> Optional[ExportFormat]:
        """
        Returns the selected export format.

        Returns:
            Optional[ExportFormat]: The selected export format.
        """

        return self.__value
