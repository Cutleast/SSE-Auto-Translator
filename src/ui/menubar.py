"""
Copyright (c) Cutleast
"""

import webbrowser
from typing import override

from cutleast_core_lib.ui.widgets.menu import Menu
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenuBar, QToolButton

from ui.utilities.icon_provider import IconProvider, ResourceIcon


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

    KOFI_URL: str = "https://ko-fi.com/cutleast"
    """URL to Ko-fi page."""

    __ko_fi_action: QAction
    __ko_fi_button: QToolButton

    @override
    def __init__(self) -> None:
        super().__init__()

        self.__init_file_menu()
        self.__init_help_menu()

        self.__ko_fi_action = QAction(self.tr("Support me on Ko-fi"))
        self.__ko_fi_action.setIcon(IconProvider.get_icon("ko-fi", set_colors=False))
        self.__ko_fi_action.setObjectName("ko-fi")
        self.__ko_fi_action.setToolTip(MenuBar.KOFI_URL)
        self.__ko_fi_action.triggered.connect(lambda: webbrowser.open(MenuBar.KOFI_URL))

        self.__ko_fi_button = QToolButton()
        self.__ko_fi_button.setDefaultAction(self.__ko_fi_action)
        self.__ko_fi_button.setAutoRaise(True)
        self.__ko_fi_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.setCornerWidget(self.__ko_fi_button, Qt.Corner.TopRightCorner)

    def __init_file_menu(self) -> None:
        file_menu = Menu(title=self.tr("File"))
        self.addMenu(file_menu)

        settings_action: QAction = file_menu.addAction(self.tr("Settings"))
        IconProvider.bind_qta_icon(settings_action, settings_action.setIcon, "mdi6.cog")
        settings_action.triggered.connect(self.settings_requested.emit)

        file_menu.addSeparator()

        exit_action: QAction = file_menu.addAction(self.tr("Exit"))
        IconProvider.bind_icon(exit_action, exit_action.setIcon, "exit")
        exit_action.triggered.connect(self.exit_requested.emit)

    def __init_help_menu(self) -> None:
        help_menu = Menu(title=self.tr("Help"))
        self.addMenu(help_menu)

        documentation_action: QAction = help_menu.addAction(
            self.tr("Show documentation...")
        )
        IconProvider.bind_qta_icon(
            documentation_action, documentation_action.setIcon, "mdi6.note-text"
        )
        documentation_action.triggered.connect(self.docs_requested.emit)

        update_action: QAction = help_menu.addAction(self.tr("Check for updates..."))
        IconProvider.bind_qta_icon(update_action, update_action.setIcon, "mdi6.refresh")
        update_action.triggered.connect(self.update_check_requested.emit)
        # update_action.setEnabled(Updater.has_instance())  # TODO: Fix being called before the Updater is initialized

        help_menu.addSeparator()

        path_limit_action: QAction = help_menu.addAction(
            self.tr("Fix Windows path limit...")
        )
        IconProvider.bind_qta_icon(
            path_limit_action, path_limit_action.setIcon, "mdi6.bug-check"
        )
        path_limit_action.triggered.connect(self.path_limit_fix_requested.emit)

        help_menu.addSeparator()

        discord_action = help_menu.addAction(
            self.tr("Get support on our Discord server...")
        )
        IconProvider.bind_icon(discord_action, discord_action.setIcon, "discord")
        discord_action.setToolTip(MenuBar.DISCORD_URL)
        discord_action.triggered.connect(lambda: webbrowser.open(MenuBar.DISCORD_URL))

        nm_action = help_menu.addAction(self.tr("Open mod page on Nexus Mods..."))
        nm_action.setIcon(IconProvider.get_res_icon(ResourceIcon.NexusMods))
        nm_action.setToolTip(MenuBar.NEXUSMODS_URL)
        nm_action.triggered.connect(lambda: webbrowser.open(MenuBar.NEXUSMODS_URL))

        github_action = help_menu.addAction(self.tr("View source code on GitHub..."))
        IconProvider.bind_qta_icon(github_action, github_action.setIcon, "mdi6.github")
        github_action.setToolTip(MenuBar.GITHUB_URL)
        github_action.triggered.connect(lambda: webbrowser.open(MenuBar.GITHUB_URL))

        help_menu.addSeparator()

        about_action: QAction = help_menu.addAction(self.tr("About"))
        IconProvider.bind_qta_icon(
            about_action, about_action.setIcon, "mdi6.information"
        )
        about_action.triggered.connect(self.about_requested.emit)

        about_qt_action: QAction = help_menu.addAction(self.tr("About Qt"))
        IconProvider.bind_icon(about_qt_action, about_qt_action.setIcon, "qt")
        about_qt_action.triggered.connect(self.about_qt_requested.emit)
