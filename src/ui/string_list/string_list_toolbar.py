"""
Copyright (c) Cutleast
"""

from typing import cast, override

from cutleast_core_lib.ui.widgets.menu import Menu
from cutleast_core_lib.ui.widgets.menu_checkbox import MenuCheckBox
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QCheckBox, QToolBar, QToolButton, QWidgetAction

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

    __filter_action: QAction
    __filter_menu: Menu
    __filter_items: dict[StringStatus, QCheckBox]

    @override
    def __init__(self) -> None:
        super().__init__()

        self.setFloatable(False)

        self.__init_filter_actions()

    def __init_filter_actions(self) -> None:
        self.__filter_menu = Menu()

        self.__filter_items = {}
        for status in StringStatus:
            filter_box = MenuCheckBox(status.get_localized_name(), self.__filter_menu)
            filter_box.setChecked(True)
            filter_box.stateChanged.connect(lambda *_: self.__on_filter_change())
            widget_action = QWidgetAction(self.__filter_menu)
            widget_action.setDefaultWidget(filter_box)
            self.__filter_menu.addAction(widget_action)

            self.__filter_items[status] = filter_box

        self.__filter_action = self.addAction(self.tr("Filter options"))
        IconProvider.bind_qta_icon(
            self.__filter_action, self.__filter_action.setIcon, "mdi6.filter"
        )
        self.__filter_action.setMenu(self.__filter_menu)
        self.__filter_action.triggered.connect(
            lambda: cast(
                QToolButton, self.widgetForAction(self.__filter_action)
            ).showMenu()
        )
        self.addAction(self.__filter_action)

    def __on_filter_change(self) -> None:
        self.filter_changed.emit(
            [
                status
                for status, checkbox in self.__filter_items.items()
                if checkbox.isChecked()
            ]
        )

    def set_filter_action_visible(self, visible: bool) -> None:
        """
        Sets the visibility of the filter action.

        Args:
            visible (bool): Whether the filter action should be visible.
        """

        self.__filter_action.setVisible(visible)
