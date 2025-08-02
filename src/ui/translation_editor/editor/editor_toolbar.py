"""
Copyright (c) Cutleast
"""

from typing import Any

from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QCheckBox, QToolBar, QWidgetAction

from core.string.string import String
from ui.utilities.icon_provider import IconProvider
from ui.widgets.menu import Menu


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

    help_requested = Signal()
    """Signal emitted when the user clicks on the help action."""

    legacy_import_requested = Signal()
    """Signal emitted when the user clicks on the import legacy action."""

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
    __filter_items: dict[String.Status, QCheckBox]

    __search_and_replace_action: QAction
    __api_translation_action: QAction

    def __init__(self) -> None:
        super().__init__()

        self.setIconSize(QSize(32, 32))
        self.setFloatable(False)

        self.__init_filter_actions()
        self.__init_actions()
        self.__init_save_actions()

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

        filter_action: QAction = self.addAction(
            IconProvider.get_qta_icon("mdi6.filter"), self.tr("Filter Options")
        )
        filter_action.setMenu(self.__filter_menu)
        filter_action.triggered.connect(
            lambda: self.__filter_menu.exec(self.mapToGlobal(self.pos()))
        )
        self.addAction(filter_action)

        help_action: QAction = self.addAction(
            IconProvider.get_qta_icon("mdi6.help"), self.tr("Help")
        )
        help_action.triggered.connect(self.help_requested.emit)

        self.addSeparator()

    def __init_actions(self) -> None:
        import_legacy_action: QAction = self.addAction(
            IconProvider.get_qta_icon("ri.inbox-archive-fill"),
            self.tr("Import pre-v1.1 Translation..."),
        )
        import_legacy_action.triggered.connect(self.legacy_import_requested.emit)

        apply_database_action: QAction = self.addAction(
            IconProvider.get_qta_icon("mdi6.database-refresh-outline"),
            self.tr("Apply Database to untranslated Strings"),
        )
        apply_database_action.triggered.connect(self.apply_database_requested.emit)

        self.__search_and_replace_action = self.addAction(
            IconProvider.get_qta_icon("msc.replace"), self.tr("Search and Replace")
        )
        self.__search_and_replace_action.triggered.connect(
            self.search_and_replace_requested.emit
        )
        self.__search_and_replace_action.setDisabled(True)

        self.__api_translation_action = self.addAction(
            IconProvider.get_qta_icon("ri.translate"), self.tr("Translate with API")
        )
        self.__api_translation_action.triggered.connect(
            self.api_translation_requested.emit
        )
        self.__api_translation_action.setDisabled(True)

        self.addSeparator()

    def __init_save_actions(self) -> None:
        save_action = self.addAction(
            IconProvider.get_qta_icon("fa5s.save"), self.tr("Save")
        )
        save_action.triggered.connect(self.save_requested.emit)

        export_action = self.addAction(
            IconProvider.get_qta_icon("fa5s.share"), self.tr("Export translation")
        )
        export_action.triggered.connect(self.export_requested.emit)

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
