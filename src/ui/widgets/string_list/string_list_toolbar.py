"""
Copyright (c) Cutleast
"""

from typing import Any

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QCheckBox, QToolBar, QWidgetAction

from core.string.string import String
from ui.utilities.icon_provider import IconProvider
from ui.widgets.menu import Menu


class StringListToolbar(QToolBar):
    """
    Toolbar for `StringListWidget`.
    """

    __parent: "StringListWidget"

    __filter_menu: Menu
    __filter_items: dict[String.Status, QCheckBox]

    def __init__(self, parent: "StringListWidget") -> None:
        super().__init__(parent)

        self.__parent = parent

        self.setIconSize(QSize(32, 32))
        self.setFloatable(False)

        self.__init_filter_actions()

    def __init_filter_actions(self) -> None:
        self.__filter_menu = Menu()

        self.__filter_items = {}
        for status in String.Status:
            filter_box = QCheckBox(
                status.get_localized_filter_name(), self.__filter_menu
            )
            filter_box.setChecked(True)
            filter_box.stateChanged.connect(self.__on_filter_change)
            widget_action = QWidgetAction(self.__filter_menu)
            widget_action.setDefaultWidget(filter_box)
            self.__filter_menu.addAction(widget_action)

            self.__filter_items[status] = filter_box

        filter_action = self.addAction(
            IconProvider.get_qta_icon("mdi6.filter"), self.tr("Filter Options")
        )
        filter_action.setMenu(self.__filter_menu)
        filter_action.triggered.connect(
            lambda: self.__filter_menu.exec(self.mapToGlobal(self.pos()))
        )
        self.addAction(filter_action)

    def __on_filter_change(self, *args: Any) -> None:
        self.__parent.set_state_filter(
            [
                status
                for status, checkbox in self.__filter_items.items()
                if checkbox.isChecked()
            ]
        )


if __name__ == "__main__":
    from .string_list_widget import StringListWidget
