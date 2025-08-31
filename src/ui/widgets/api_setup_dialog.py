"""
Copyright (c) Cutleast
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QVBoxLayout

from .api_setup import ApiSetup


class ApiSetupDialog(QDialog):
    """
    Dialog for setting up the Nexus Mods API key.
    """

    __vlayout: QVBoxLayout
    __api_setup: ApiSetup
    __save_button: QPushButton

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(self.tr("Setup Nexus Mods API key..."))
        self.setMinimumSize(800, 400)

        self.__init_ui()

        self.__api_setup.valid_signal.connect(self.__save_button.setEnabled)
        self.__save_button.clicked.connect(self.accept)

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.__vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.__vlayout)

        self.__init_setup()

        self.__vlayout.addStretch()

        self.__init_footer()

    def __init_setup(self) -> None:
        self.__api_setup = ApiSetup()
        self.__vlayout.addWidget(self.__api_setup)

    def __init_footer(self) -> None:
        hlayout = QHBoxLayout()
        hlayout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.__vlayout.addLayout(hlayout)

        self.__save_button = QPushButton(self.tr("Save"))
        self.__save_button.setDefault(True)
        self.__save_button.setDisabled(True)
        hlayout.addWidget(self.__save_button)

        cancel_button = QPushButton(self.tr("Cancel"))
        cancel_button.clicked.connect(self.reject)
        hlayout.addWidget(cancel_button)

    def get_api_key(self) -> str:
        """
        Returns:
            str: The setup API key.

        Raises:
            ValueError: If the API key is None.
        """

        key: Optional[str] = self.__api_setup.api_key

        if key is None:
            raise ValueError("API key is None!")

        return key
