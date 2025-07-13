"""
Copyright (c) Cutleast
"""

from typing import Any, Optional

from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QCheckBox, QToolBar, QWidgetAction

from app_context import AppContext
from core.mod_file.translation_status import TranslationStatus
from ui.utilities.icon_provider import IconProvider, ResourceIcon
from ui.widgets.menu import Menu


class MainToolBar(QToolBar):
    """
    Toolbar for main page.
    """

    filter_changed = Signal(list)
    """
    Signal emitted when the user changes the checked filters.

    Args:
        list[TranslationStatus]: List of checked filters
    """

    ignore_list_requested = Signal()
    """Signal when the user clicks on the ignore list action."""

    help_requested = Signal()
    """Signal when the user clicks on the help action."""

    modlist_scan_requested = Signal()
    """Signal when the user clicks on the modlist scan action."""

    online_scan_requested = Signal()
    """Signal when the user clicks on the online scan action."""

    download_requested = Signal()
    """Signal when the user clicks on the download action."""

    build_output_requested = Signal()
    """Signal when the user clicks on the build output action."""

    deep_scan_requested = Signal()
    """Signal when the user clicks on the deep scan action."""

    string_search_requested = Signal()
    """Signal when the user clicks on the string search action."""

    __filter_menu: Menu
    __filter_items: dict[TranslationStatus, QCheckBox]

    __modlist_scan_action: QAction
    __online_scan_action: QAction
    __download_action: QAction
    __build_output_action: QAction

    __deep_scan_action: QAction
    __string_search_action: QAction

    def __init__(self) -> None:
        super().__init__()

        self.setIconSize(QSize(32, 32))
        self.setFloatable(False)

        self.__init_filter_actions()
        self.__init_actions()
        self.__init_search_actions()

        self.__highlight_action(self.__modlist_scan_action)

    def __init_filter_actions(self) -> None:
        self.__filter_menu = Menu()

        self.__filter_items = {}
        for status in TranslationStatus:
            filter_box = QCheckBox(
                status.get_localized_filter_name(), self.__filter_menu
            )
            filter_box.setObjectName("menu_checkbox")
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

        open_ignore_list_action = self.addAction(
            IconProvider.get_qta_icon("mdi6.playlist-remove"),
            self.tr("Open ignore list"),
        )
        open_ignore_list_action.triggered.connect(self.ignore_list_requested.emit)

        help_action = self.addAction(
            IconProvider.get_qta_icon("mdi6.help"), self.tr("Help")
        )
        help_action.triggered.connect(self.help_requested.emit)

        self.addSeparator()

    def __init_actions(self) -> None:
        self.__modlist_scan_action = self.addAction(
            IconProvider.get_res_icon(ResourceIcon.DetectLang),
            self.tr("Scan modlist..."),
        )
        self.__modlist_scan_action.triggered.connect(self.__on_modlist_scan_requested)

        self.__online_scan_action = self.addAction(
            IconProvider.get_res_icon(ResourceIcon.ScanOnline),
            self.tr("Scan Online for available translations..."),
        )
        self.__online_scan_action.triggered.connect(self.__on_online_scan_requested)

        self.__download_action = self.addAction(
            IconProvider.get_qta_icon("mdi6.download-multiple"),
            self.tr("Download available translations..."),
        )
        self.__download_action.triggered.connect(self.__on_download_requested)

        self.__build_output_action = self.addAction(
            IconProvider.get_qta_icon("mdi6.export-variant"),
            self.tr("Build output mod..."),
        )
        self.__build_output_action.triggered.connect(self.__on_build_output_requested)

        self.addSeparator()

    def __init_search_actions(self) -> None:
        self.__deep_scan_action = self.addAction(
            IconProvider.get_qta_icon("mdi6.line-scan"),
            self.tr("Scan translations for missing strings..."),
        )
        self.__deep_scan_action.triggered.connect(self.deep_scan_requested.emit)

        self.__string_search_action = self.addAction(
            IconProvider.get_qta_icon("mdi6.layers-search"),
            self.tr("Search modlist for string..."),
        )
        self.__string_search_action.triggered.connect(self.string_search_requested.emit)

    def __on_filter_change(self, *args: Any) -> None:
        self.filter_changed.emit(
            [
                status
                for status, checkbox in self.__filter_items.items()
                if checkbox.isChecked()
            ]
        )

    def __on_modlist_scan_requested(self) -> None:
        self.modlist_scan_requested.emit()
        self.__highlight_action(self.__online_scan_action)

    def __on_online_scan_requested(self) -> None:
        self.online_scan_requested.emit()
        self.__highlight_action(self.__download_action)

    def __on_download_requested(self) -> None:
        self.download_requested.emit()
        self.__highlight_action(self.__build_output_action)

    def __on_build_output_requested(self) -> None:
        self.build_output_requested.emit()
        self.__highlight_action(None)

    def __highlight_action(self, action: Optional[QAction]) -> None:
        """
        Highlights a toolbar action and unhighlights the others.

        Args:
            action (Optional[QAction]):
                The action to highlight or None if no action should be highlighted.
        """

        for _action in self.actions():
            self.widgetForAction(_action).setObjectName("")

        if action is not None:
            self.widgetForAction(action).setObjectName("accent_button")

        # Reapply stylesheet (the full stylesheet is required as the toolbar doesn't
        # initially have its own)
        self.setStyleSheet(AppContext.get_app().styleSheet())
