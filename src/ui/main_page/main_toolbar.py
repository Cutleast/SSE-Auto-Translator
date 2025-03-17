"""
Copyright (c) Cutleast
"""

from typing import Any

import qtawesome as qta
from PySide6.QtCore import QSize
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QCheckBox, QToolBar, QWidgetAction

from app_context import AppContext
from core.mod_instance.mod_file import ModFile
from ui.widgets.menu import Menu


class MainToolBar(QToolBar):
    """
    Toolbar for main page.
    """

    __parent: "MainPageWidget"

    __filter_menu: Menu
    __filter_items: dict[ModFile.Status, QCheckBox]

    modlist_scan_action: QAction
    online_scan_action: QAction
    download_action: QAction
    build_output_action: QAction

    deep_scan_action: QAction
    string_search_action: QAction

    def __init__(self, parent: "MainPageWidget"):
        super().__init__(parent)

        self.__parent = parent

        self.setIconSize(QSize(32, 32))
        self.setFloatable(False)

        self.__init_filter_actions()
        self.__init_actions()
        self.__init_search_actions()

    def __init_filter_actions(self) -> None:
        self.__filter_menu = Menu()

        self.__filter_items = {}
        for status in ModFile.Status:
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
            qta.icon("mdi6.filter", color=self.palette().text().color()),
            self.tr("Filter Options"),
        )
        filter_action.setMenu(self.__filter_menu)
        filter_action.triggered.connect(
            lambda: self.__filter_menu.exec(self.mapToGlobal(self.pos()))
        )
        self.addAction(filter_action)

        open_ignore_list_action = self.addAction(
            qta.icon("mdi6.playlist-remove", color=self.palette().text().color()),
            self.tr("Open plugin ignore list"),
        )
        open_ignore_list_action.triggered.connect(self.__parent.open_ignore_list)

        help_action = self.addAction(
            qta.icon("mdi6.help", color=self.palette().text().color()), self.tr("Help")
        )
        help_action.triggered.connect(self.__parent.show_help)

        self.addSeparator()

    def __init_actions(self) -> None:
        self.modlist_scan_action = self.addAction(
            QIcon(":/icons/detect_lang.svg"), self.tr("Scan modlist...")
        )
        self.widgetForAction(self.modlist_scan_action).setObjectName("accent_button")
        self.modlist_scan_action.triggered.connect(self.__parent.basic_scan)

        self.online_scan_action = self.addAction(
            QIcon(":/icons/scan_online.svg"),
            self.tr("Scan Online for available translations..."),
        )
        self.online_scan_action.triggered.connect(self.__parent.online_scan)

        self.download_action = self.addAction(
            qta.icon("mdi6.download-multiple", color=self.palette().text().color()),
            self.tr("Download available translations..."),
        )
        self.download_action.triggered.connect(
            self.__parent.download_and_install_translations
        )

        self.build_output_action = self.addAction(
            qta.icon("mdi6.export-variant", color=self.palette().text().color()),
            self.tr("Build output mod..."),
        )
        self.build_output_action.triggered.connect(self.__parent.build_output)

        self.addSeparator()

    def __init_search_actions(self) -> None:
        self.deep_scan_action = self.addAction(
            qta.icon("mdi6.line-scan", color=self.palette().text().color()),
            self.tr("Scan translations for missing strings..."),
        )
        self.deep_scan_action.triggered.connect(self.__parent.deep_scan)

        self.string_search_action = self.addAction(
            qta.icon("mdi6.layers-search", color=self.palette().text().color()),
            self.tr("Search modlist for string..."),
        )
        self.string_search_action.triggered.connect(self.__parent.run_string_search)

    def __on_filter_change(self, *args: Any) -> None:
        self.__parent.set_state_filter(
            [
                status
                for status, checkbox in self.__filter_items.items()
                if checkbox.isChecked()
            ]
        )

    def highlight_action(self, action: QAction) -> None:
        """
        Highlights a toolbar action and unhighlights the others.

        Args:
            action (QAction): The action to highlight
        """

        for _action in self.actions():
            self.widgetForAction(_action).setObjectName("")
        self.widgetForAction(action).setObjectName("accent_button")

        # Reapply stylesheet
        self.setStyleSheet(AppContext.get_app().styleSheet())


if __name__ == "__main__":
    from .main_page import MainPageWidget
