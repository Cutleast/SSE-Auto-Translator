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

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.sso_button = qtw.QPushButton(self.mloc.sso_setup)
        self.sso_button.setCheckable(True)

        def goto_sso():
            self.sso_button.setChecked(True)
            self.manual_button.setChecked(False)
            api_key_box.hide()
            sso_box.show()

        self.sso_button.clicked.connect(goto_sso)
        hlayout.addWidget(self.sso_button)

        sso_box = qtw.QWidget()
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
        sso_button.setDisabled(True)
        sso_button.setToolTip("WIP")
        sso_vlayout.addWidget(sso_button)
        vlayout.addWidget(sso_box)

        self.manual_button = qtw.QPushButton(self.mloc.manual_setup)
        self.manual_button.setCheckable(True)

        def goto_manual():
            self.manual_button.setChecked(True)
            self.sso_button.setChecked(False)
            sso_box.hide()
            api_key_box.show()

        self.manual_button.clicked.connect(goto_manual)
        hlayout.addWidget(self.manual_button)

        api_key_box = qtw.QWidget()
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
        vlayout.addWidget(api_key_box)

        self.sso_button.click()
