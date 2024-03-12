"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import qtpy.QtCore as qtc
import qtpy.QtWidgets as qtw

from main import MainApp
from nm_api import NexusModsApi

from .paste_entry import PasteLineEdit


class ApiSetup(qtw.QWidget):
    """
    Widget for API Setup.
    """

    valid_signal = qtc.Signal(bool)
    is_valid: bool = False
    api_key: str = None

    def __init__(self, app: MainApp):
        super().__init__()

        self.app = app
        self.loc = app.loc
        self.mloc = self.loc.api_setup

        vlayout = qtw.QVBoxLayout()
        vlayout.setAlignment(qtc.Qt.AlignmentFlag.AlignTop)
        self.setLayout(vlayout)

        vlayout.addSpacing(25)

        api_help_label = qtw.QLabel(self.mloc.api_help)
        api_help_label.setWordWrap(True)
        vlayout.addWidget(api_help_label)

        vlayout.addSpacing(25)

        tab_widget = qtw.QTabWidget()
        tab_widget.tabBar().setExpanding(True)
        tab_widget.setObjectName("centered_tab")
        vlayout.addWidget(tab_widget)

        sso_box = qtw.QWidget()
        sso_box.setObjectName("transparent")
        sso_vlayout = qtw.QVBoxLayout()
        sso_box.setLayout(sso_vlayout)
        sso_button = qtw.QPushButton(self.mloc.start_sso)

        def start_sso():
            api = NexusModsApi("")
            api.log.addHandler(app.log_handler)
            api.log.setLevel(app.log_level)
            self.api_key = api.get_sso_key()
            sso_button.setText(self.mloc.sso_successful)
            self.setDisabled(True)
            self.is_valid = True
            self.valid_signal.emit(True)

        sso_button.clicked.connect(start_sso)
        sso_vlayout.addWidget(sso_button)
        tab_widget.addTab(sso_box, self.mloc.sso_setup)

        api_key_box = qtw.QWidget()
        api_key_box.setObjectName("transparent")
        api_key_vlayout = qtw.QVBoxLayout()
        api_key_box.setLayout(api_key_vlayout)
        api_key_hlayout = qtw.QHBoxLayout()
        api_key_vlayout.addLayout(api_key_hlayout)
        api_key_label = qtw.QLabel(self.mloc.insert_api_key)
        api_key_hlayout.addWidget(api_key_label)
        self.api_key_entry = PasteLineEdit()
        api_key_hlayout.addWidget(self.api_key_entry)
        api_key_check_button = qtw.QPushButton(self.mloc.check_api_key)

        def check_api_key():
            key = self.api_key_entry.text().strip()

            if not key:
                return

            api_key_check_button.setText("Checking API Key...")
            if NexusModsApi(key).check_api_key():
                self.api_key = key
                self.is_valid = True
                self.valid_signal.emit(True)
                api_key_check_button.setText("API Key valid!")
                self.setDisabled(True)
            else:
                self.is_valid = False
                self.valid_signal.emit(False)
                api_key_check_button.setText("API Key invalid! Please try again!")

        api_key_check_button.clicked.connect(check_api_key)
        api_key_vlayout.addWidget(api_key_check_button)
        tab_widget.addTab(api_key_box, self.mloc.manual_setup)
