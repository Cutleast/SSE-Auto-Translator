"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.ui.widgets.menu import Menu
from PySide6.QtCore import QSize, Signal
from PySide6.QtWidgets import QCheckBox, QToolBar, QWidgetAction

from core.string.string_status import StringStatus
from ui.utilities.icon_provider import IconProvider


class StringListToolbar(QToolBar):
    """
    Toolbar for `StringListWidget`.
    """

    filter_changed = Signal(list)
    """
    Signal emitted when the user changes the display filter.

    Args:
        list[StringStatus]: The list of selected string states to display.
    """

    __filter_menu: Menu
    __filter_items: dict[StringStatus, QCheckBox]

    @override
    def __init__(self) -> None:
        super().__init__()

        self.setIconSize(QSize(32, 32))
        self.setFloatable(False)

        self.__init_filter_actions()

    def __init_filter_actions(self) -> None:
        self.__filter_menu = Menu()

        self.__filter_items = {}
        for status in StringStatus:
            filter_box = QCheckBox(
                status.get_localized_filter_name(), self.__filter_menu
            )
            filter_box.setChecked(True)
            filter_box.stateChanged.connect(lambda *_: self.__on_filter_change())
            widget_action = QWidgetAction(self.__filter_menu)
            widget_action.setDefaultWidget(filter_box)
            self.__filter_menu.addAction(widget_action)

            self.__filter_items[status] = filter_box

        filter_action = self.addAction(
            IconProvider.get_qta_icon("mdi6.filter"), self.tr("Filter options")
        )
        filter_action.setMenu(self.__filter_menu)
        filter_action.triggered.connect(
            lambda: self.__filter_menu.exec(self.mapToGlobal(self.pos()))
        )
        self.addAction(filter_action)

    def __on_filter_change(self) -> None:
        self.filter_changed.emit(
            [
                status
                for status, checkbox in self.__filter_items.items()
                if checkbox.isChecked()
            ]
        )
