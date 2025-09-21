"""
Copyright (c) Cutleast
"""

from cutleast_core_lib.ui.widgets.menu import Menu
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QCursor
from PySide6.QtWidgets import QTreeWidgetItem

from ui.utilities.icon_provider import IconProvider

from .download_list_item import DownloadListItem


class DownloadListMenu(Menu):
    """
    Context menu for the download list widget.
    """

    expand_all_clicked = Signal()
    """Signal emitted when the expand all button is clicked."""

    collapse_all_clicked = Signal()
    """Signal emitted when the collapse all button is clicked."""

    check_selected_clicked = Signal()
    """Signal emitted when the check selected button is clicked."""

    uncheck_selected_clicked = Signal()
    """Signal emitted when the uncheck selected button is clicked."""

    __check_action: QAction
    __uncheck_action: QAction

    def __init__(self) -> None:
        super().__init__()

        self.__init_item_actions()

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

        self.__uncheck_action = self.addAction(self.tr("Uncheck selected download(s)"))
        self.__uncheck_action.setIcon(IconProvider.get_qta_icon("mdi6.close"))
        self.__uncheck_action.triggered.connect(self.uncheck_selected_clicked.emit)

        self.__check_action = self.addAction(self.tr("Check selected download(s)"))
        self.__check_action.setIcon(IconProvider.get_qta_icon("mdi6.check"))
        self.__check_action.triggered.connect(self.check_selected_clicked.emit)

    def open(self, selected_items: list[QTreeWidgetItem]) -> None:
        """
        Opens the context menu at the current cursor position.

        Args:
            selected_items (list[QTreeWidgetItem]): List of currently selected items.
        """

        self.__uncheck_action.setEnabled(
            any(
                isinstance(i, DownloadListItem) and i.is_checked()
                for i in selected_items
            )
        )
        self.__check_action.setEnabled(
            any(
                isinstance(i, DownloadListItem) and not i.is_checked()
                for i in selected_items
            )
        )

        self.exec(QCursor.pos())
