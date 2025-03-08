"""
Copyright (c) Cutleast
"""

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMenuBar, QMessageBox

from app_context import AppContext
from core.utilities.path_limit_fixer import PathLimitFixer
from core.utilities.updater import Updater

from .settings.settings_dialog import SettingsDialog
from .widgets.about_dialog import AboutDialog
from .widgets.menu import Menu


class MenuBar(QMenuBar):
    """
    Menu bar for main window.
    """

    def __init__(self) -> None:
        super().__init__()

        file_menu = Menu(title=self.tr("File"))
        self.addMenu(file_menu)

        settings_action = file_menu.addAction(self.tr("Settings"))
        settings_action.setIcon(qta.icon("mdi6.cog", color="#ffffff"))
        settings_action.triggered.connect(self.__open_settings)

        file_menu.addSeparator()

        exit_action = file_menu.addAction(self.tr("Exit"))
        exit_action.setIcon(QIcon(":/icons/exit.svg"))
        exit_action.triggered.connect(QApplication.exit)

        help_menu = Menu(title=self.tr("Help"))
        self.addMenu(help_menu)

        documentation_action = help_menu.addAction(self.tr("Show Documentation..."))
        documentation_action.setIcon(qta.icon("mdi6.note-text", color="#ffffff"))
        documentation_action.triggered.connect(AppContext.get_app().open_documentation)

        update_action = help_menu.addAction(self.tr("Check for updates..."))
        update_action.setIcon(qta.icon("fa.refresh", color="#ffffff"))
        update_action.triggered.connect(self.__check_for_updates)

        help_menu.addSeparator()

        path_limit_action = help_menu.addAction(self.tr("Fix Windows Path Limit..."))
        path_limit_action.setIcon(
            qta.icon(
                "mdi6.bug-check", color=self.palette().text().color(), scale_factor=1.3
            )
        )
        path_limit_action.triggered.connect(
            lambda: PathLimitFixer.disable_path_limit(AppContext.get_app().res_path)
        )

        help_menu.addSeparator()

        about_action = help_menu.addAction(self.tr("About"))
        about_action.setIcon(qta.icon("fa5s.info-circle", color="#ffffff"))
        about_action.triggered.connect(self.__show_about)

        about_qt_action = help_menu.addAction(self.tr("About Qt"))
        about_qt_action.triggered.connect(self.__show_about_qt)

    def __open_settings(self) -> None:
        SettingsDialog().exec()

    def __check_for_updates(self) -> None:
        upd = Updater(AppContext.get_app().APP_VERSION)
        if upd.update_available():
            upd.run()
        else:
            messagebox = QMessageBox(AppContext.get_app().main_window)
            messagebox.setWindowTitle(self.tr("No Updates Available"))
            messagebox.setText(self.tr("There are no updates available."))
            messagebox.setTextFormat(Qt.TextFormat.RichText)
            messagebox.setIcon(QMessageBox.Icon.Information)
            messagebox.exec()

    def __show_about(self) -> None:
        AboutDialog(AppContext.get_app().main_window).exec()

    def __show_about_qt(self) -> None:
        QMessageBox.aboutQt(AppContext.get_app().main_window, self.tr("About Qt"))
