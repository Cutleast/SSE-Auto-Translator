"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional

from cutleast_core_lib.ui.widgets.menu import Menu
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QCursor

from core.database.translation import Translation
from core.translation_provider.source import Source
from ui.utilities.icon_provider import IconProvider, ResourceIcon


class TranslationsMenu(Menu):
    """
    Context menu for translations tab.
    """

    expand_all_clicked = Signal()
    """Signal emitted when the user clicks on the expand all action."""

    collapse_all_clicked = Signal()
    """Signal emitted when the user clicks on the collapse all action."""

    show_strings_requested = Signal()
    """Signal emitted when the user clicks on the show strings action."""

    edit_translation_requested = Signal()
    """Signal emitted when the user clicks on the edit translation action."""

    rename_translation_requested = Signal()
    """Signal emitted when the user clicks on the rename translation action."""

    export_translation_requested = Signal()
    """Signal emitted when the user clicks on the export translation action."""

    delete_translation_requested = Signal()
    """Signal emitted when the user clicks on the delete translation action."""

    open_modpage_requested = Signal()
    """Signal emitted when the user clicks on the open modpage action."""

    open_in_explorer_requested = Signal()
    """Signal emitted when the user clicks on the open in explorer action."""

    __show_strings_action: QAction
    __edit_translation_action: QAction
    __rename_translation_action: QAction
    __export_translation_action: QAction
    __delete_translation_action: QAction
    __open_modpage_action: QAction
    __open_in_explorer_action: QAction

    def __init__(self) -> None:
        super().__init__()

        self.__init_item_actions()
        self.__init_translation_actions()
        self.__init_open_actions()

    def __init_item_actions(self) -> None:
        expand_all_action: QAction = self.addAction(
            IconProvider.get_qta_icon("mdi6.arrow-expand-vertical"),
            self.tr("Expand all"),
        )
        expand_all_action.triggered.connect(self.expand_all_clicked.emit)

        collapse_all_action: QAction = self.addAction(
            IconProvider.get_qta_icon("mdi6.arrow-collapse-vertical"),
            self.tr("Collapse all"),
        )
        collapse_all_action.triggered.connect(self.collapse_all_clicked.emit)

        self.addSeparator()

    def __init_translation_actions(self) -> None:
        self.__show_strings_action = self.addAction(
            IconProvider.get_qta_icon("mdi6.book-open-outline"),
            self.tr("Show translation strings..."),
        )
        self.__show_strings_action.triggered.connect(self.show_strings_requested.emit)

        self.__edit_translation_action = self.addAction(
            IconProvider.get_qta_icon("mdi6.book-edit"), self.tr("Edit translation...")
        )
        self.__edit_translation_action.triggered.connect(
            self.edit_translation_requested.emit
        )

        self.__rename_translation_action = self.addAction(
            IconProvider.get_qta_icon("mdi6.rename"), self.tr("Rename translation...")
        )
        self.__rename_translation_action.triggered.connect(
            self.rename_translation_requested.emit
        )

        self.__export_translation_action = self.addAction(
            IconProvider.get_qta_icon("fa5s.share"), self.tr("Export translation...")
        )
        self.__export_translation_action.triggered.connect(
            self.export_translation_requested.emit
        )

        self.__delete_translation_action = self.addAction(
            IconProvider.get_qta_icon("mdi6.delete"),
            self.tr("Delete selected translation(s)..."),
        )
        self.__delete_translation_action.triggered.connect(
            self.delete_translation_requested.emit
        )

        self.addSeparator()

    def __init_open_actions(self) -> None:
        self.__open_modpage_action = self.addAction(
            IconProvider.get_res_icon(ResourceIcon.NexusMods),
            self.tr("Open mod page..."),
        )
        self.__open_modpage_action.triggered.connect(self.open_modpage_requested.emit)

        self.__open_in_explorer_action = self.addAction(
            IconProvider.get_qta_icon("fa5s.folder"),
            self.tr("Open in Explorer..."),
        )
        self.__open_in_explorer_action.triggered.connect(
            self.open_in_explorer_requested.emit
        )

    def open(self, current_item: Optional[Translation | Path]) -> None:
        """
        Opens the context menu at the current cursor position.

        Args:
            current_item (Optional[Translation | Path]): The current item in the tree view.
        """

        if (
            isinstance(current_item, Translation)
            and current_item.source != Source.Local
        ):
            self.__open_modpage_action.setVisible(True)
            self.__open_modpage_action.setIcon(current_item.source.get_icon())  # type: ignore[arg-type]
        else:
            self.__open_modpage_action.setVisible(False)

        self.__show_strings_action.setVisible(isinstance(current_item, Translation))
        self.__edit_translation_action.setVisible(isinstance(current_item, Translation))
        self.__rename_translation_action.setVisible(
            isinstance(current_item, Translation)
        )
        self.__export_translation_action.setVisible(
            isinstance(current_item, Translation)
        )
        self.__delete_translation_action.setVisible(
            isinstance(current_item, Translation)
        )
        self.__open_in_explorer_action.setVisible(isinstance(current_item, Translation))

        self.exec(QCursor.pos())
