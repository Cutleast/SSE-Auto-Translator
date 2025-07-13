"""
Copyright (c) Cutleast
"""

from typing import Optional

import qtawesome as qta
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QCursor, QIcon

from core.database.translation import Translation
from core.translation_provider.source import Source
from ui.widgets.menu import Menu


class TranslationsMenu(Menu):
    """
    Context menu for translations tab.
    """

    expand_all_clicked = Signal()
    """Signal emitted when the user clicks on the expand all action."""

    collapse_all_clicked = Signal()
    """Signal emitted when the user clicks on the collapse all action."""

    ignore_updates_requested = Signal()
    """Signal emitted when the user clicks on the ignore update action."""

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

    __ignore_update_action: QAction

    def __init__(self) -> None:
        super().__init__()

        self.__init_item_actions()
        self.__init_translation_actions()
        self.__init_open_actions()

    def __init_item_actions(self) -> None:
        expand_all_action: QAction = self.addAction(
            qta.icon("mdi6.arrow-expand-vertical", color=self.palette().text().color()),
            self.tr("Expand all"),
        )
        expand_all_action.triggered.connect(self.expand_all_clicked.emit)

        collapse_all_action: QAction = self.addAction(
            qta.icon(
                "mdi6.arrow-collapse-vertical", color=self.palette().text().color()
            ),
            self.tr("Collapse all"),
        )
        collapse_all_action.triggered.connect(self.collapse_all_clicked.emit)

        self.addSeparator()

    def __init_translation_actions(self) -> None:
        self.__ignore_update_action = self.addAction(
            qta.icon("mdi6.cloud-alert", color="#ffffff"),
            self.tr("Ignore translation update"),
        )
        self.__ignore_update_action.triggered.connect(
            self.ignore_updates_requested.emit
        )

        show_strings_action: QAction = self.addAction(
            qta.icon("mdi6.book-open-outline", color="#ffffff"),
            self.tr("Show translation strings..."),
        )
        show_strings_action.triggered.connect(self.show_strings_requested.emit)

        edit_translation_action: QAction = self.addAction(
            qta.icon("mdi6.book-edit", color="#ffffff"), self.tr("Edit translation...")
        )
        edit_translation_action.triggered.connect(self.edit_translation_requested.emit)

        rename_translation_action: QAction = self.addAction(
            qta.icon("mdi6.rename", color="#ffffff"), self.tr("Rename translation...")
        )
        rename_translation_action.triggered.connect(
            self.rename_translation_requested.emit
        )

        export_translation_action: QAction = self.addAction(
            qta.icon("fa5s.share", color="#ffffff"), self.tr("Export translation...")
        )
        export_translation_action.triggered.connect(
            self.export_translation_requested.emit
        )

        delete_translation_action: QAction = self.addAction(
            qta.icon("mdi6.delete", color="#ffffff"),
            self.tr("Delete selected translation(s)..."),
        )
        delete_translation_action.triggered.connect(
            self.delete_translation_requested.emit
        )

        self.addSeparator()

    def __init_open_actions(self) -> None:
        self.__open_modpage_action: QAction = self.addAction(
            QIcon(":/icons/nexus_mods.svg"), self.tr("Open mod page...")
        )
        self.__open_modpage_action.triggered.connect(self.open_modpage_requested.emit)

        open_in_explorer_action: QAction = self.addAction(
            qta.icon("fa5s.folder", color="#ffffff"),
            self.tr("Open in Explorer..."),
        )
        open_in_explorer_action.triggered.connect(self.open_in_explorer_requested.emit)

    def open(self, current_item: Optional[Translation | str]) -> None:
        """
        Opens the context menu at the current cursor position.

        Args:
            current_item (Optional[Translation | str]): The current item in the tree view.
        """

        if (
            isinstance(current_item, Translation)
            and current_item.source is not None
            and current_item.source != Source.Local
        ):
            self.__open_modpage_action.setVisible(True)
            self.__open_modpage_action.setIcon(current_item.source.get_icon())  # type: ignore[arg-type]
        else:
            self.__open_modpage_action.setVisible(False)

        self.__ignore_update_action.setVisible(
            isinstance(current_item, Translation)
            and current_item.status == Translation.Status.UpdateAvailable
        )

        self.exec(QCursor.pos())
