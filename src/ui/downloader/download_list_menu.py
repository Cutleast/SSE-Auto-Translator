"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.ui.widgets.tree_menu import TreeMenu
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QTreeWidgetItem

from ui.utilities.icon_provider import IconProvider

from .download_list_item import DownloadListItem


class DownloadListMenu(TreeMenu):
    """
    Context menu for the download list widget.
    """

    check_selected_clicked = Signal()
    """Signal emitted when the check selected button is clicked."""

    uncheck_selected_clicked = Signal()
    """Signal emitted when the uncheck selected button is clicked."""

    __check_action: QAction
    __uncheck_action: QAction

    @override
    def __init__(self) -> None:
        super().__init__()

        self.__init_item_actions()

    def __init_item_actions(self) -> None:
        self.__uncheck_action = self.addAction(self.tr("Uncheck selected download(s)"))
        IconProvider.bind_qta_icon(
            self.__uncheck_action, self.__uncheck_action.setIcon, "mdi6.close"
        )
        self.__uncheck_action.triggered.connect(self.uncheck_selected_clicked.emit)

        self.__check_action = self.addAction(self.tr("Check selected download(s)"))
        IconProvider.bind_qta_icon(
            self.__check_action, self.__check_action.setIcon, "mdi6.check"
        )
        self.__check_action.triggered.connect(self.check_selected_clicked.emit)

    @override
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

        super().open()
