"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import os
from typing import override

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
)

from app_context import AppContext

from .app_settings import AppSettings
from .translator_settings import TranslatorSettings
from .user_settings import UserSettings


class SettingsDialog(QDialog):
    """
    Class for Settings dialog.

    TODO: Overhaul backend and UI
    """

    changes_pending: bool = False

    log: logging.Logger = logging.getLogger("Settings")

    def __init__(self) -> None:
        super().__init__(QApplication.activeModalWidget())

        self.setModal(True)
        self.setWindowTitle(self.tr("Settings"))
        self.setObjectName("root")
        self.setMinimumSize(1000, 650)
        self.resize(1000, 650)

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        title_label = QLabel(self.tr("Settings"))
        title_label.setObjectName("title_label")
        vlayout.addWidget(title_label)

        vlayout.addSpacing(20)

        restart_hint_label = QLabel(
            self.tr("A restart is required for the changes to take effect.")
        )
        restart_hint_label.setObjectName("relevant_label")
        vlayout.addWidget(restart_hint_label)

        vlayout.addSpacing(20)

        tab_widget = QTabWidget()
        tab_widget.tabBar().setExpanding(True)
        tab_widget.tabBar().setDocumentMode(True)
        vlayout.addWidget(tab_widget)

        self.app_settings = AppSettings()
        self.app_settings.on_change_signal.connect(self.on_change)
        tab_widget.addTab(self.app_settings, self.tr("App Settings"))

        self.user_settings = UserSettings()
        self.user_settings.on_change_signal.connect(self.on_change)
        tab_widget.addTab(self.user_settings, self.tr("User Settings"))

        self.translator_settings = TranslatorSettings()
        self.translator_settings.on_change_signal.connect(self.on_change)
        tab_widget.addTab(self.translator_settings, self.tr("Translator Settings"))

        vlayout.addStretch()
        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        hlayout.addStretch()

        self.save_button = QPushButton(self.tr("Save"))
        self.save_button.clicked.connect(self.save)
        self.save_button.setObjectName("accent_button")
        self.save_button.setDefault(True)
        self.save_button.setDisabled(True)
        hlayout.addWidget(self.save_button)

        cancel_button = QPushButton(self.tr("Cancel"))
        cancel_button.clicked.connect(self.close)
        hlayout.addWidget(cancel_button)

    def on_change(self) -> None:
        """
        Sets `changes_pending` to `True`.
        """

        self.changes_pending = True
        self.save_button.setDisabled(False)
        self.setWindowTitle(self.tr("Settings") + "*")

    @override
    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Cancels dialog and asks for confirmation
        if changes are pending.
        """

        if self.changes_pending:
            message_box = QMessageBox(self)
            message_box.setWindowTitle(self.tr("Cancel"))
            message_box.setText(
                self.tr("Are you sure you want to cancel? All changes will be lost.")
            )
            message_box.setStandardButtons(
                QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(QMessageBox.StandardButton.Yes)
            message_box.button(QMessageBox.StandardButton.No).setText(self.tr("No"))
            message_box.button(QMessageBox.StandardButton.No).setObjectName(
                "accent_button"
            )
            message_box.button(QMessageBox.StandardButton.Yes).setText(self.tr("Yes"))
            choice = message_box.exec()

            if choice == QMessageBox.StandardButton.Yes:
                self.accept()
            elif event:
                event.ignore()
        else:
            self.accept()

    def save(self) -> None:
        """
        Saves settings and closes dialog.
        """

        self.app_settings.save_settings()
        self.user_settings.save_settings()
        self.translator_settings.save_settings()

        # TODO: Replace validation by try-except-blocks for ValueErrors
        # if app_settings["output_path"] is not None:
        #     if os.path.isdir(app_settings["output_path"]):
        #         files = os.listdir(app_settings["output_path"])

        #         # Only warn about a path that contains
        #         # folders other than an SKSE folder
        #         # (which is then very likely an already existing output folder)
        #         if files and files != ["SKSE"]:
        #             messagebox = QMessageBox()
        #             apply_dark_title_bar(messagebox)
        #             messagebox.setIcon(messagebox.Icon.Warning)
        #             messagebox.setWindowTitle(self.loc.main.warning)
        #             messagebox.setText(self.mloc.output_path_not_empty)
        #             messagebox.setStandardButtons(
        #                 QMessageBox.StandardButton.Yes
        #                 | QMessageBox.StandardButton.Cancel
        #             )
        #             messagebox.button(QMessageBox.StandardButton.Cancel).setText(
        #                 self.loc.main.cancel
        #             )
        #             messagebox.button(QMessageBox.StandardButton.Yes).setText(
        #                 self.loc.main._continue
        #             )
        #             choice = messagebox.exec()

        #             if choice != QMessageBox.StandardButton.Yes:
        #                 return

        # if (
        #     translator_settings["translator"] == "DeepL"
        #     and not translator_settings["api_key"]
        # ):
        #     ErrorDialog(
        #         self,
        #         self.app,
        #         self.mloc.empty_translator_api_key,
        #         self.mloc.empty_translator_api_key_text,
        #     ).exec()
        #     return

        # path_file = self.app.data_path / "user" / "portable.txt"
        # if user_settings["modinstance"] == "Portable":
        #     instance_path = self.user_settings.instance_path_entry.text().strip()
        #     ini_path = Path(instance_path) / "ModOrganizer.ini"

        #     if ini_path.is_file() and instance_path:
        #         path_file.write_text(instance_path)
        #     else:
        #         ErrorDialog(
        #             self,
        #             self.app,
        #             self.mloc.invalid_path,
        #             self.mloc.invalid_path_text,
        #             yesno=False,
        #         ).exec()
        #         return
        # elif path_file.is_file():
        #     os.remove(path_file)

        # with open(self.app.app_conf_path, "w", encoding="utf8") as file:
        #     json.dump(app_settings, file, indent=4)

        # with open(self.app.user_conf_path, "w", encoding="utf8") as file:
        #     json.dump(user_settings, file, indent=4)

        # with open(self.app.translator_conf_path, "w", encoding="utf8") as file:
        #     json.dump(translator_settings, file, indent=4)

        # self.app.app_config = app_settings
        # self.app.user_config = user_settings
        # self.app.translator_config = translator_settings

        self.accept()

        self.log.info("New settings saved. Changes will take effect after a restart.")

        if self.changes_pending:
            messagebox = QMessageBox()
            messagebox.setWindowTitle(self.tr("Restart required"))
            messagebox.setText(
                self.tr(
                    "SSE-AT must be restarted for the changes to take effect! Restart now?"
                )
            )
            messagebox.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            messagebox.button(QMessageBox.StandardButton.No).setText(self.tr("No"))
            messagebox.button(QMessageBox.StandardButton.Yes).setText(self.tr("Yes"))
            choice = messagebox.exec()

            if choice == QMessageBox.StandardButton.Yes:
                exe_path: str = AppContext.get_app().get_execution_command()
                if os.path.isfile(exe_path):
                    os.startfile(exe_path)
                QApplication.exit()
