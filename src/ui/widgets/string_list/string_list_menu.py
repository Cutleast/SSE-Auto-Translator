"""
Copyright (c) Cutleast
"""

from PySide6.QtGui import QAction, QCursor, QKeySequence
from PySide6.QtWidgets import QCheckBox, QWidgetAction

from core.database.string import String
from ui.utilities.icon_provider import IconProvider
from ui.widgets.menu import Menu


class StringListMenu(Menu):
    """
    Context menu for `StringListWidget`.
    """

    __parent: "StringListWidget"

    __copy_menu: Menu
    __copy_checkboxes: dict[int, QCheckBox]
    """
    Map for column index and copy checkbox.
    """

    def __init__(self, parent: "StringListWidget", nested: bool = True) -> None:
        super().__init__()

        self.__parent = parent

        if nested:
            self.__init_separator_actions()

        self.__init_copy_menu()

    def __init_separator_actions(self) -> None:
        expand_all_action: QAction = self.addAction(
            IconProvider.get_qta_icon("mdi6.arrow-expand-vertical"),
            self.tr("Expand all"),
        )
        expand_all_action.triggered.connect(self.__parent.expandAll)

        collapse_all_action: QAction = self.addAction(
            IconProvider.get_qta_icon("mdi6.arrow-collapse-vertical"),
            self.tr("Collapse all"),
        )
        collapse_all_action.triggered.connect(self.__parent.collapseAll)

        self.addSeparator()

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

        # TODO: Hide translated string column if translation mode is False
        self.__copy_checkboxes = {}
        for c, column in enumerate(self.__parent.columns):
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

        self.__parent.copy_selected(selected_column_indexes)

    def open(self) -> None:
        """
        Opens the context menu at the current cursor position.
        """

        selected_strings: list[String] = self.__parent.get_selected_items()

        self.__copy_menu.menuAction().setVisible(len(selected_strings) > 0)

        self.exec(QCursor.pos())


if __name__ == "__main__":
    from .string_list_widget import StringListWidget
