"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.ui.widgets.menu import Menu
from cutleast_core_lib.ui.widgets.tree_menu import TreeMenu
from PySide6.QtCore import Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QCheckBox, QWidgetAction

from ui.utilities.icon_provider import IconProvider


class StringListMenu(TreeMenu):
    """
    Context menu for `StringListWidget`.
    """

    copy_selected_requested = Signal(list[int])
    """
    Signal emitted when the user requests to copy the selected strings.

    Args:
        list[int]: The list of selected column indexes to copy.
    """

    __columns: list[str]
    __nested: bool

    __copy_menu: Menu
    __copy_checkboxes: dict[int, QCheckBox]
    """
    Map for column index and copy checkbox.
    """

    def __init__(self, columns: list[str], nested: bool = True) -> None:
        """
        Args:
            columns (list[str]): The list of column names.
            nested (bool, optional):
                If the string list has separators. Defaults to True.
        """

        super().__init__()

        self.__columns = columns
        self.__nested = nested

        self.__init_copy_menu()

    def __init_copy_menu(self) -> None:
        self.__copy_menu = Menu(
            IconProvider.get_qta_icon("mdi6.content-copy"), self.tr("Copy")
        )
        self.addMenu(self.__copy_menu)

        copy_all_action = self.__copy_menu.addAction(
            IconProvider.get_qta_icon("mdi6.content-copy"), self.tr("Copy")
        )
        copy_all_action.setShortcut(QKeySequence("Ctrl+C"))
        copy_all_action.triggered.connect(self.__copy)

        self.__copy_menu.addSeparator()

        self.__copy_checkboxes = {}
        for c, column in enumerate(self.__columns):
            checkbox = QCheckBox(self.tr("Copy {0}").format(column), self.__copy_menu)
            checkbox.setChecked(True)
            widget_action = QWidgetAction(self.__copy_menu)
            widget_action.setDefaultWidget(checkbox)
            self.__copy_menu.addAction(widget_action)

            self.__copy_checkboxes[c] = checkbox

    def __copy(self) -> None:
        selected_column_indexes: list[int] = [
            c for c, checkbox in self.__copy_checkboxes.items() if checkbox.isChecked()
        ]

        self.copy_selected_requested.emit(selected_column_indexes)

    @override
    def open(self, selected_string_count: int) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Opens the context menu at the current cursor position.

        Args:
            selected_string_count (int):
                The number of selected strings in the string list.
        """

        self.__copy_menu.menuAction().setVisible(selected_string_count > 0)

        super().open(expandable=self.__nested)
