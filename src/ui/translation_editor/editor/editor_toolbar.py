"""
Copyright (c) Cutleast
"""

from typing import Any, cast, override

from cutleast_core_lib.ui.widgets.menu import Menu
from cutleast_core_lib.ui.widgets.menu_checkbox import MenuCheckBox
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QCheckBox, QToolBar, QToolButton, QWidgetAction

from core.string.string_status import StringStatus
from ui.utilities.icon_provider import IconProvider


class EditorToolbar(QToolBar):
    """
    Toolbar for an editor tab.
    """

    filter_changed = Signal(list)
    """
    Signal emitted when the user changes the checked filters.

    Args:
        list[Status]: List of checked filters
    """

    apply_database_requested = Signal()
    """Signal emitted when the user clicks on the apply database action."""

    search_and_replace_requested = Signal()
    """Signal emitted when the user clicks on the search and replace action."""

    api_translation_requested = Signal()
    """Signal emitted when the user clicks on the API translation action."""

    save_requested = Signal()
    """Signal emitted when the user clicks on the save action."""

    export_requested = Signal()
    """Signal emitted when the user clicks on the export action."""

    __filter_menu: Menu
    __filter_items: dict[StringStatus, QCheckBox]

    __search_and_replace_action: QAction
    __api_translation_action: QAction

    @override
    def __init__(self) -> None:
        super().__init__()

        self.setFloatable(False)

        self.__init_save_actions()
        self.__init_translation_actions()
        self.__init_filter_actions()

    def __init_save_actions(self) -> None:
        save_action = self.addAction(self.tr("Save"))
        IconProvider.bind_qta_icon(save_action, save_action.setIcon, "mdi6.content-save")
        save_action.triggered.connect(self.save_requested.emit)

        export_action = self.addAction(self.tr("Export translation"))
        IconProvider.bind_qta_icon(export_action, export_action.setIcon, "mdi6.share")
        export_action.triggered.connect(self.export_requested.emit)

        self.addSeparator()

    def __init_translation_actions(self) -> None:
        apply_database_action: QAction = self.addAction(
            self.tr("Apply database to untranslated strings")
        )
        IconProvider.bind_qta_icon(
            apply_database_action,
            apply_database_action.setIcon,
            "mdi6.database-refresh-outline",
        )
        apply_database_action.triggered.connect(self.apply_database_requested.emit)

        self.__search_and_replace_action = self.addAction(self.tr("Search and replace"))
        IconProvider.bind_qta_icon(
            self.__search_and_replace_action,
            self.__search_and_replace_action.setIcon,
            "mdi6.find-replace",
        )
        self.__search_and_replace_action.triggered.connect(
            self.search_and_replace_requested.emit
        )
        self.__search_and_replace_action.setDisabled(True)

        self.__api_translation_action = self.addAction(self.tr("Translate with API"))
        IconProvider.bind_qta_icon(
            self.__api_translation_action,
            self.__api_translation_action.setIcon,
            "mdi6.translate",
        )
        self.__api_translation_action.triggered.connect(
            self.api_translation_requested.emit
        )
        self.__api_translation_action.setDisabled(True)

        self.addSeparator()

    def __init_filter_actions(self) -> None:
        self.__filter_menu = Menu()

        self.__filter_items = {}
        for status in StringStatus:
            filter_box = MenuCheckBox(status.get_localized_name(), self.__filter_menu)
            filter_box.setChecked(True)
            filter_box.stateChanged.connect(self.__on_filter_change)
            widget_action = QWidgetAction(self.__filter_menu)
            widget_action.setDefaultWidget(filter_box)
            self.__filter_menu.addAction(widget_action)

            self.__filter_items[status] = filter_box

        filter_action: QAction = self.addAction(self.tr("Filter options"))
        IconProvider.bind_qta_icon(filter_action, filter_action.setIcon, "mdi6.filter")
        filter_action.setMenu(self.__filter_menu)
        filter_action.triggered.connect(
            lambda: cast(QToolButton, self.widgetForAction(filter_action)).showMenu()
        )
        self.addAction(filter_action)

    def __on_filter_change(self, *args: Any) -> None:
        self.filter_changed.emit(
            [
                status
                for status, filter_box in self.__filter_items.items()
                if filter_box.isChecked()
            ]
        )

    def set_edit_actions_enabled(self, enabled: bool) -> None:
        """
        Set the enabled state of the edit actions api translation and search and replace.

        Args:
            enabled (bool): Whether the actions should be enabled.
        """

        self.__search_and_replace_action.setEnabled(enabled)
        self.__api_translation_action.setEnabled(enabled)
