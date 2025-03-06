"""
Copyright (c) Cutleast
"""

from typing import Any

import qtawesome as qta
from PySide6.QtCore import QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QCheckBox, QToolBar, QWidgetAction

from core.database.string import String
from ui.widgets.menu import Menu


class EditorToolbar(QToolBar):
    """
    Toolbar for an editor tab.
    """

    __parent: "EditorTab"

    __filter_menu: Menu
    __filter_items: dict[String.Status, QCheckBox]

    import_legacy_action: QAction
    apply_database_action: QAction
    search_and_replace_action: QAction
    api_translation_action: QAction

    def __init__(self, parent: "EditorTab"):
        super().__init__(parent)

        self.__parent = parent

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
            filter_box.setObjectName("menu_checkbox")
            filter_box.setChecked(True)
            filter_box.stateChanged.connect(self.__on_filter_change)
            widget_action = QWidgetAction(self.__filter_menu)
            widget_action.setDefaultWidget(filter_box)
            self.__filter_menu.addAction(widget_action)

            self.__filter_items[status] = filter_box

        filter_action: QAction = self.addAction(
            qta.icon("mdi6.filter", color="#ffffff"),
            self.tr("Filter Options"),
        )
        filter_action.setMenu(self.__filter_menu)
        filter_action.triggered.connect(
            lambda: self.__filter_menu.exec(self.mapToGlobal(self.pos()))
        )
        self.addAction(filter_action)

        help_action: QAction = self.addAction(
            qta.icon("mdi6.help", color="#ffffff"), self.tr("Help")
        )
        help_action.triggered.connect(self.__parent.show_help)

        self.addSeparator()

    def __init_actions(self) -> None:
        self.import_legacy_action = self.addAction(
            qta.icon("ri.inbox-archive-fill", color="#ffffff"),
            self.tr("Import pre-v1.1 Translation..."),
        )
        self.import_legacy_action.triggered.connect(self.__parent.import_legacy)

        self.apply_database_action = self.addAction(
            qta.icon("mdi6.database-refresh-outline", color="#ffffff"),
            self.tr("Apply Database to untranslated Strings"),
        )
        self.apply_database_action.triggered.connect(self.__parent.apply_database)

        self.search_and_replace_action = self.addAction(
            qta.icon("msc.replace", color="#ffffff"), self.tr("Search and Replace")
        )
        self.search_and_replace_action.triggered.connect(
            self.__parent.search_and_replace
        )
        self.search_and_replace_action.setDisabled(True)

        self.api_translation_action = self.addAction(
            qta.icon("ri.translate", color="#ffffff"), self.tr("Translate with API")
        )
        self.api_translation_action.triggered.connect(self.__parent.translate_with_api)
        self.api_translation_action.setDisabled(True)

        self.addSeparator()

    def __init_save_actions(self) -> None:
        save_action = self.addAction(
            qta.icon("fa5s.save", color="#ffffff"), self.tr("Save")
        )
        save_action.triggered.connect(self.__parent.save)

        export_action = self.addAction(
            qta.icon("fa5s.share", color="#ffffff"), self.tr("Export translation")
        )
        export_action.triggered.connect(self.__parent.export)

    def __on_filter_change(self, *args: Any) -> None:
        self.__parent.set_state_filter(
            [
                status
                for status, filter_box in self.__filter_items.items()
                if filter_box.isChecked()
            ]
        )


if __name__ == "__main__":
    from .editor_tab import EditorTab
