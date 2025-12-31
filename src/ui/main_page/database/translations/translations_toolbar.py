"""
Copyright (c) Cutleast
"""

from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar

from ui.utilities.icon_provider import IconProvider


class TranslationsToolbar(QToolBar):
    """
    Toolbar for translations tab.
    """

    show_vanilla_strings_requested = Signal()
    """Signal emitted when the user clicks on the show vanilla strings action."""

    search_database_requested = Signal()
    """Signal emitted when the user clicks on the search database action."""

    local_import_requested = Signal()
    """Signal emitted when the user clicks on the local import action."""

    def __init__(self) -> None:
        super().__init__()

        self.setIconSize(QSize(32, 32))
        self.setFloatable(False)

        self.__init_actions()

    def __init_actions(self) -> None:
        show_vanilla_strings_action: QAction = self.addAction(
            IconProvider.get_qta_icon("mdi6.book-open-outline"),
            self.tr("Show base game (+ AE CC content) strings"),
        )
        show_vanilla_strings_action.triggered.connect(
            self.show_vanilla_strings_requested.emit
        )

        search_database_action: QAction = self.addAction(
            IconProvider.get_icon("search"), self.tr("Search database")
        )
        search_database_action.triggered.connect(self.search_database_requested.emit)

        self.addSeparator()

        local_import_action: QAction = self.addAction(
            IconProvider.get_qta_icon("mdi6.import"),
            self.tr("Import translation from local disk"),
        )
        local_import_action.triggered.connect(self.local_import_requested.emit)
