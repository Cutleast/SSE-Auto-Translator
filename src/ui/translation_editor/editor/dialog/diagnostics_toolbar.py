"""
Copyright (c) Cutleast
"""

from typing import Any, cast, override

from cutleast_core_lib.ui.widgets.menu import Menu
from cutleast_core_lib.ui.widgets.menu_checkbox import MenuCheckBox
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QCheckBox, QToolBar, QToolButton, QWidgetAction

from core.editor.models import Severity
from ui.utilities.icon_provider import IconProvider


class DiagnosticsToolBar(QToolBar):
    """
    Toolbar for the diagnostics section of the translator dialog.
    """

    filter_changed = Signal(list)
    """
    Signal emitted when the user changes the checked filters.

    Args:
        list[Status]: List of checked filters.
    """

    __filter_action: QAction
    __filter_menu: Menu
    __filter_items: dict[Severity, QCheckBox]

    @override
    def __init__(self) -> None:
        super().__init__()

        self.setFloatable(False)

        self.__init_filter_actions()

    def __init_filter_actions(self) -> None:
        self.__filter_menu = Menu()

        self.__filter_items = {}
        for severity in Severity:
            if severity == Severity.Passed:
                continue  # there are no "passed" issues to filter

            filter_box = MenuCheckBox(severity.get_localized_name(), self.__filter_menu)
            filter_box.setChecked(True)
            filter_box.stateChanged.connect(self.__on_filter_change)
            widget_action = QWidgetAction(self.__filter_menu)
            widget_action.setDefaultWidget(filter_box)
            self.__filter_menu.addAction(widget_action)

            self.__filter_items[severity] = filter_box

        self.__filter_action = self.addAction(self.tr("Filter options"))
        IconProvider.bind_qta_icon(
            self.__filter_action, self.__filter_action.setIcon, "mdi6.filter"
        )
        self.__filter_action.setCheckable(True)
        self.__filter_action.setMenu(self.__filter_menu)
        self.__filter_action.triggered.connect(self.__on_filter_action_triggered)

    def __on_filter_action_triggered(self) -> None:
        # reverse the checked state
        self.__filter_action.setChecked(not self.__filter_action.isChecked())

        cast(QToolButton, self.widgetForAction(self.__filter_action)).showMenu()

    def __on_filter_change(self, *args: Any) -> None:
        filters: list[Severity] = [
            status
            for status, filter_box in self.__filter_items.items()
            if filter_box.isChecked()
        ]

        self.__filter_action.setChecked(
            len(filters) != len(self.__filter_items) and len(filters) > 0
        )
        self.filter_changed.emit(filters)
