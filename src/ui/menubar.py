"""
Copyright (c) Cutleast
"""

import os
from pathlib import Path

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMenuBar, QMessageBox

from app_context import AppContext
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

        exit_action = file_menu.addAction(self.tr("Exit"))
        exit_action.setIcon(qta.icon("fa5s.window-close", color="#ffffff"))
        exit_action.triggered.connect(QApplication.exit)

        settings_action = self.addAction(self.tr("Settings"))
        settings_action.triggered.connect(self.__open_settings)

        help_menu = Menu(title=self.tr("Help"))
        self.addMenu(help_menu)

        documentation_action = help_menu.addAction(self.tr("Show Documentation..."))
        documentation_action.setIcon(qta.icon("mdi6.note-text", color="#ffffff"))
        documentation_action.triggered.connect(self.__show_documentation)

        update_action = help_menu.addAction(self.tr("Check for updates..."))
        update_action.setIcon(qta.icon("fa.refresh", color="#ffffff"))
        update_action.triggered.connect(self.__check_for_updates)

        help_menu.addSeparator()

        path_limit_action = help_menu.addAction(self.tr("Fix Windows Path Limit..."))
        path_limit_action.triggered.connect(self.__fix_path_limit)

        help_menu.addSeparator()

        about_action = help_menu.addAction(self.tr("About"))
        about_action.setIcon(qta.icon("fa5s.info-circle", color="#ffffff"))
        about_action.triggered.connect(self.__show_about)

        about_qt_action = help_menu.addAction(self.tr("About Qt"))
        about_qt_action.triggered.connect(self.__show_about_qt)

    def __show_documentation(self) -> None:
        exe_path: str = AppContext.get_app().executable
        os.startfile(exe_path, arguments="--show-docs")

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

    def __fix_path_limit(self) -> None:
        res_path: Path = AppContext.get_app().res_path

        try:
            os.startfile(res_path / "path_limit.reg")
        except OSError:
            pass

    def __show_about(self) -> None:
        AboutDialog(AppContext.get_app().main_window).exec()

    def __show_about_qt(self) -> None:
        QMessageBox.aboutQt(AppContext.get_app().main_window, self.tr("About Qt"))