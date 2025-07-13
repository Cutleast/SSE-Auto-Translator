"""
Copyright (c) Cutleast
"""

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenuBar

from ui.utilities.icon_provider import IconProvider, ResourceIcon

from .widgets.menu import Menu


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
        exit_action.setIcon(IconProvider.get_res_icon(ResourceIcon.Exit))
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

        help_menu.addSeparator()

        path_limit_action: QAction = help_menu.addAction(
            self.tr("Fix Windows Path Limit...")
        )
        path_limit_action.setIcon(IconProvider.get_qta_icon("mdi6.bug-check"))
        path_limit_action.triggered.connect(self.path_limit_fix_requested.emit)

        help_menu.addSeparator()

        about_action: QAction = help_menu.addAction(self.tr("About"))
        about_action.setIcon(IconProvider.get_qta_icon("fa5s.info-circle"))
        about_action.triggered.connect(self.about_qt_requested.emit)

        about_qt_action: QAction = help_menu.addAction(self.tr("About Qt"))
        about_qt_action.triggered.connect(self.about_requested.emit)
