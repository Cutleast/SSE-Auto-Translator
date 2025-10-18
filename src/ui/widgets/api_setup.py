"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.translation_provider.nm_api.nm_api import NexusModsApi

from .paste_entry import PasteLineEdit


class ApiSetup(QWidget):
    """
    Widget for API Setup.
    """

    valid_signal = Signal(bool)
    is_valid: bool = False
    api_key: Optional[str] = None

    def __init__(self) -> None:
        super().__init__()

        vlayout = QVBoxLayout()
        vlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(vlayout)

        api_help_label = QLabel(
            self.tr(
                "In order to get translations from Nexus Mods this tool needs access "
                "to the Nexus Mods API. You can setup access by two methods: "
                "insert API key manually or via SSO (Single-Sign-On)."
            )
        )
        api_help_label.setWordWrap(True)
        vlayout.addWidget(api_help_label)

        vlayout.addSpacing(10)

        tab_widget = QTabWidget()
        tab_widget.tabBar().setExpanding(True)
        tab_widget.setObjectName("centered_tab")
        vlayout.addWidget(tab_widget)

        sso_box = QWidget()
        sso_box.setObjectName("transparent")
        sso_vlayout = QVBoxLayout()
        sso_box.setLayout(sso_vlayout)
        sso_button = QPushButton(
            self.tr("Click here to login to Nexus Mods via browser")
        )

        def start_sso() -> None:
            api = NexusModsApi()
            self.api_key = api.get_sso_key()
            sso_button.setText(self.tr("Successfully logged into Nexus Mods"))
            self.setDisabled(True)
            self.is_valid = True
            self.valid_signal.emit(True)

        sso_button.clicked.connect(start_sso)
        sso_vlayout.addWidget(sso_button)
        tab_widget.addTab(sso_box, self.tr("Single-Sign-On (browser)"))

        api_key_box = QWidget()
        api_key_box.setObjectName("transparent")
        api_key_vlayout = QVBoxLayout()
        api_key_box.setLayout(api_key_vlayout)
        api_key_hlayout = QHBoxLayout()
        api_key_vlayout.addLayout(api_key_hlayout)
        api_key_label = QLabel(self.tr("Insert your API key"))
        api_key_hlayout.addWidget(api_key_label)
        self.api_key_entry = PasteLineEdit()
        api_key_hlayout.addWidget(self.api_key_entry)
        api_key_check_button = QPushButton(self.tr("Check API key"))

        def check_api_key() -> None:
            key = self.api_key_entry.text().strip()

            if not key:
                return

            api_key_check_button.setText("Checking API key...")
            if NexusModsApi().is_api_key_valid(key):
                self.api_key = key
                self.is_valid = True
                self.valid_signal.emit(True)
                api_key_check_button.setText(self.tr("API key is valid!"))
                self.setDisabled(True)
            else:
                self.is_valid = False
                self.valid_signal.emit(False)
                api_key_check_button.setText(self.tr("API key is invalid!"))

        api_key_check_button.clicked.connect(check_api_key)
        api_key_vlayout.addWidget(api_key_check_button)
        tab_widget.addTab(api_key_box, self.tr("Manual Setup"))
