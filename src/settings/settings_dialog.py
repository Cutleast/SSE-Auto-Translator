"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import os
from pathlib import Path

import jstyleson as json
import qtpy.QtWidgets as qtw

import utilities as utils
from main import MainApp
from widgets import ErrorDialog

from .app_settings import AppSettings
from .translator_settings import TranslatorSettings
from .user_settings import UserSettings


class SettingsDialog(qtw.QDialog):
    """
    Class for Settings dialog.
    """

    changes_pending: bool = False

    log = logging.getLogger("Settings")

    def __init__(self, app: MainApp):
        super().__init__(app.root)

        self.app = app
        self.loc = app.loc
        self.mloc = app.loc.settings

        self.setModal(True)
        self.setWindowTitle(self.mloc.settings)
        self.setObjectName("root")
        self.setMinimumSize(1000, 600)
        self.resize(1000, 600)

        utils.apply_dark_title_bar(self)

        vlayout = qtw.QVBoxLayout()
        self.setLayout(vlayout)

        title_label = qtw.QLabel(self.mloc.settings)
        title_label.setObjectName("title_label")
        vlayout.addWidget(title_label)

        vlayout.addSpacing(20)

        restart_hint_label = qtw.QLabel(self.mloc.restart_hint)
        restart_hint_label.setObjectName("relevant_label")
        vlayout.addWidget(restart_hint_label)

        vlayout.addSpacing(20)

        tab_widget = qtw.QTabWidget()
        tab_widget.tabBar().setExpanding(True)
        tab_widget.tabBar().setDocumentMode(True)
        vlayout.addWidget(tab_widget)

        self.app_settings = AppSettings(app)
        self.app_settings.on_change_signal.connect(self.on_change)
        tab_widget.addTab(self.app_settings, self.mloc.app_settings)

        self.user_settings = UserSettings(app)
        self.user_settings.on_change_signal.connect(self.on_change)
        tab_widget.addTab(self.user_settings, self.mloc.user_settings)

        self.translator_settings = TranslatorSettings(app)
        self.translator_settings.on_change_signal.connect(self.on_change)
        tab_widget.addTab(self.translator_settings, self.mloc.translator_settings)

        vlayout.addStretch()
        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        hlayout.addStretch()

        self.save_button = qtw.QPushButton(self.loc.main.save)
        self.save_button.clicked.connect(self.save)
        self.save_button.setObjectName("accent_button")
        self.save_button.setDefault(True)
        self.save_button.setDisabled(True)
        hlayout.addWidget(self.save_button)

        cancel_button = qtw.QPushButton(self.loc.main.cancel)
        cancel_button.clicked.connect(self.close)
        hlayout.addWidget(cancel_button)

    def on_change(self):
        """
        Sets `changes_pending` to `True`.
        """

        self.changes_pending = True
        self.save_button.setDisabled(False)
        self.setWindowTitle(self.mloc.settings + "*")

    def closeEvent(self, event):
        """
        Cancels dialog and asks for confirmation
        if changes are pending.
        """

        if self.changes_pending:
            message_box = qtw.QMessageBox(self)
            utils.apply_dark_title_bar(message_box)
            message_box.setWindowTitle(self.loc.main.cancel)
            message_box.setText(self.loc.main.cancel_text)
            message_box.setStandardButtons(
                qtw.QMessageBox.StandardButton.No | qtw.QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(qtw.QMessageBox.StandardButton.No)
            message_box.button(qtw.QMessageBox.StandardButton.No).setText(
                self.loc.main.no
            )
            message_box.button(qtw.QMessageBox.StandardButton.No).setObjectName("accent_button")
            message_box.button(qtw.QMessageBox.StandardButton.Yes).setText(
                self.loc.main.yes
            )
            choice = message_box.exec()

            if choice == qtw.QMessageBox.StandardButton.Yes:
                self.accept()
            elif event:
                event.ignore()
        else:
            self.accept()

    def save(self):
        """
        Saves settings and closes dialog.
        """

        app_settings = self.app_settings.get_settings()
        user_settings = self.user_settings.get_settings()
        translator_settings = self.translator_settings.get_settings()

        if translator_settings["translator"] == "DeepL" and not translator_settings["api_key"]:
            ErrorDialog(
                self,
                self.app,
                self.mloc.empty_translator_api_key,
                self.mloc.empty_translator_api_key_text,
            ).exec()
            return

        path_file = self.app.data_path / "user" / "portable.txt"
        if user_settings["modinstance"] == "Portable":
            instance_path = self.user_settings.instance_path_entry.text().strip()
            ini_path = Path(instance_path) / "ModOrganizer.ini"

            if ini_path.is_file() and instance_path:
                path_file.write_text(instance_path)
            else:
                ErrorDialog(
                    self,
                    self.app,
                    self.mloc.invalid_path,
                    self.mloc.invalid_path_text,
                    yesno=False,
                ).exec()
                return
        elif path_file.is_file():
            os.remove(path_file)

        with open(self.app.app_conf_path, "w", encoding="utf8") as file:
            json.dump(app_settings, file, indent=4)

        with open(self.app.user_conf_path, "w", encoding="utf8") as file:
            json.dump(user_settings, file, indent=4)

        with open(self.app.translator_conf_path, "w", encoding="utf8") as file:
            json.dump(translator_settings, file, indent=4)

        self.app.app_config = app_settings
        self.app.user_config = user_settings
        self.app.translator_config = translator_settings

        self.accept()

        self.log.info(
            "New settings saved. Changes will take effect after a restart."
        )

        if self.changes_pending:
            messagebox = qtw.QMessageBox()
            utils.apply_dark_title_bar(messagebox)
            messagebox.setWindowTitle(self.mloc.restart_title)
            messagebox.setText(self.mloc.restart_text)
            messagebox.setStandardButtons(
                qtw.QMessageBox.StandardButton.Yes | qtw.QMessageBox.StandardButton.No
            )
            messagebox.button(qtw.QMessageBox.StandardButton.No).setText(
                self.loc.main.no
            )
            messagebox.button(qtw.QMessageBox.StandardButton.Yes).setText(
                self.loc.main.yes
            )
            choice = messagebox.exec()

            if choice == qtw.QMessageBox.StandardButton.Yes:
                os.startfile(self.app.executable)
                self.app.exit()
