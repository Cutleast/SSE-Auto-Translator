"""
Copyright (c) Cutleast
"""

from typing import override

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

    update_translations_requested = Signal()
    """Signal emitted when the user clicks on the update translations action."""

    @override
    def __init__(self) -> None:
        super().__init__()

        self.setIconSize(QSize(24, 24))
        self.setFloatable(False)

        self.__init_actions()

    def __init_actions(self) -> None:
        show_vanilla_strings_action: QAction = self.addAction(
            self.tr("Show base game (+ AE CC content) strings"),
        )
        IconProvider.bind_qta_icon(
            show_vanilla_strings_action,
            show_vanilla_strings_action.setIcon,
            "mdi6.book-open-outline",
        )
        show_vanilla_strings_action.triggered.connect(
            self.show_vanilla_strings_requested.emit
        )

        search_database_action: QAction = self.addAction(self.tr("Search database"))
        IconProvider.bind_icon(
            search_database_action, search_database_action.setIcon, "search"
        )
        search_database_action.triggered.connect(self.search_database_requested.emit)

        self.addSeparator()

        local_import_action: QAction = self.addAction(
            self.tr("Import translation from local disk")
        )
        IconProvider.bind_qta_icon(
            local_import_action, local_import_action.setIcon, "mdi6.import"
        )
        local_import_action.triggered.connect(self.local_import_requested.emit)

        update_translations_action: QAction = self.addAction(
            self.tr("Update translations from installed mods")
        )
        IconProvider.bind_qta_icon(
            update_translations_action,
            update_translations_action.setIcon,
            "mdi6.book-refresh-outline",
        )
        update_translations_action.triggered.connect(
            self.update_translations_requested.emit
        )
