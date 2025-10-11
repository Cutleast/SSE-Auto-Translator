"""
Copyright (c) Cutleast
"""

import webbrowser

from cutleast_core_lib.ui.widgets.menu import Menu
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenuBar

from ui.utilities.icon_provider import IconProvider


class MenuBar(QMenuBar):
    """
    Menu bar for main window.
    """

    settings_requested = Signal()
    """Signal emitted when the user clicks on the settings action."""

    exit_requested = Signal()
    """Signal emitted when the user clicks on the exit action."""

    update_check_requested = Signal()
    """Signal emitted when the user clicks on the check for updates action."""

    docs_requested = Signal()
    """Signal emitted when the user clicks on the documentation action."""

    path_limit_fix_requested = Signal()
    """Signal emitted when the user clicks on the fix path limit action."""

    about_requested = Signal()
    """Signal emitted when the user clicks on the about action."""

    about_qt_requested = Signal()
    """Signal emitted when the user clicks on the about Qt action."""

    DISCORD_URL: str = "https://discord.gg/pqEHdWDf8z"
    """URL to our Discord server."""

    NEXUSMODS_URL: str = "https://www.nexusmods.com/skyrimspecialedition/mods/111491"
    """URL to SSE-AT's Nexus Mods page."""

    GITHUB_URL: str = "https://github.com/Cutleast/SSE-Auto-Translator"
    """URL to the GitHub repository."""

    def __init__(self) -> None:
        super().__init__()

        self.__init_file_menu()
        self.__init_help_menu()

    def __init_file_menu(self) -> None:
        file_menu = Menu(title=self.tr("File"))
        self.addMenu(file_menu)

        settings_action: QAction = file_menu.addAction(self.tr("Settings"))
        settings_action.setIcon(IconProvider.get_qta_icon("mdi6.cog"))
        settings_action.triggered.connect(self.settings_requested.emit)

        file_menu.addSeparator()

        exit_action: QAction = file_menu.addAction(self.tr("Exit"))
        exit_action.setIcon(IconProvider.get_icon("exit"))
        exit_action.triggered.connect(self.exit_requested.emit)

    def __init_help_menu(self) -> None:
        help_menu = Menu(title=self.tr("Help"))
        self.addMenu(help_menu)

        documentation_action: QAction = help_menu.addAction(
            self.tr("Show Documentation...")
        )
        documentation_action.setIcon(IconProvider.get_qta_icon("mdi6.note-text"))
        documentation_action.triggered.connect(self.docs_requested.emit)

        update_action: QAction = help_menu.addAction(self.tr("Check for updates..."))
        update_action.setIcon(IconProvider.get_qta_icon("mdi6.refresh"))
        update_action.triggered.connect(self.update_check_requested.emit)
        # update_action.setEnabled(Updater.has_instance())  # TODO: Fix being called before the Updater is initialized

        help_menu.addSeparator()

        path_limit_action: QAction = help_menu.addAction(
            self.tr("Fix Windows Path Limit...")
        )
        path_limit_action.setIcon(IconProvider.get_qta_icon("mdi6.bug-check"))
        path_limit_action.triggered.connect(self.path_limit_fix_requested.emit)

        help_menu.addSeparator()

        discord_action = help_menu.addAction(
            self.tr("Get support on our Discord server...")
        )
        discord_action.setIcon(IconProvider.get_icon("discord"))
        discord_action.setToolTip(MenuBar.DISCORD_URL)
        discord_action.triggered.connect(lambda: webbrowser.open(MenuBar.DISCORD_URL))

        nm_action = help_menu.addAction(self.tr("Open mod page on Nexus Mods..."))
        nm_action.setIcon(QIcon(":/icons/nexus_mods_colored.png"))
        nm_action.setToolTip(MenuBar.NEXUSMODS_URL)
        nm_action.triggered.connect(lambda: webbrowser.open(MenuBar.NEXUSMODS_URL))

        github_action = help_menu.addAction(self.tr("View source code on GitHub..."))
        github_action.setIcon(IconProvider.get_qta_icon("mdi6.github"))
        github_action.setToolTip(MenuBar.GITHUB_URL)
        github_action.triggered.connect(lambda: webbrowser.open(MenuBar.GITHUB_URL))

        help_menu.addSeparator()

        about_action: QAction = help_menu.addAction(self.tr("About"))
        about_action.setIcon(IconProvider.get_qta_icon("fa5s.info-circle"))
        about_action.triggered.connect(self.about_requested.emit)

        about_qt_action: QAction = help_menu.addAction(self.tr("About Qt"))
        about_qt_action.triggered.connect(self.about_qt_requested.emit)
