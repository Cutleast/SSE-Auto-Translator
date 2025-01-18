"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app_context import AppContext
from core.masterlist.masterlist import Masterlist
from core.masterlist.masterlist_entry import MasterlistEntry
from core.utilities import matches_filter
from core.utilities.constants import AE_CC_PLUGINS, BASE_GAME_PLUGINS

from .search_bar import SearchBar


class IgnoreListDialog(QDialog):
    """
    Dialog for ignore lists.
    """

    masterlist: Masterlist

    __userlist_widget: QListWidget
    __remove_button: QPushButton

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.masterlist = AppContext.get_app().masterlist

        self.setWindowTitle(self.tr("Ignore list"))
        self.resize(600, 500)

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        tab_widget = QTabWidget()
        tab_widget.setObjectName("centered_tab")
        vlayout.addWidget(tab_widget)

        user_tab = QWidget()
        user_tab.setObjectName("transparent")
        tab_widget.addTab(user_tab, self.tr("User ignore list"))

        vlayout = QVBoxLayout()
        user_tab.setLayout(vlayout)

        self.__remove_button = QPushButton(self.tr("Remove selected plugins from list"))
        self.__remove_button.setDisabled(True)
        self.__remove_button.clicked.connect(self.__remove_selected)
        vlayout.addWidget(self.__remove_button)

        self.__userlist_widget = QListWidget()
        self.__userlist_widget.setAlternatingRowColors(True)
        self.__userlist_widget.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection
        )
        self.__userlist_widget.setUniformItemSizes(True)
        self.__userlist_widget.itemSelectionChanged.connect(self.__on_select)
        self.__userlist_widget.addItems(self.masterlist.user_ignore_list)
        vlayout.addWidget(self.__userlist_widget)

        search_bar = SearchBar()
        search_bar.searchChanged.connect(self.__on_text_filter_change)
        vlayout.addWidget(search_bar)

        vanilla_list_widget = QListWidget()
        vanilla_list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        vanilla_list_widget.setUniformItemSizes(True)
        vanilla_list_widget.addItems(BASE_GAME_PLUGINS + AE_CC_PLUGINS)
        tab_widget.addTab(vanilla_list_widget, self.tr("Base Game + CC Plugins"))

        masterlist_widget = QListWidget()
        masterlist_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        masterlist_widget.setUniformItemSizes(True)
        masterlist_widget.addItems(
            sorted(
                plugin
                for plugin, masterlist_entry in self.masterlist.entries.items()
                if masterlist_entry.type == MasterlistEntry.Type.Ignore
            )
        )
        tab_widget.addTab(masterlist_widget, self.tr("Masterlist Entries"))
        tab_widget.setTabEnabled(2, bool(masterlist_widget.count()))

    def __on_select(self) -> None:
        items: list[QListWidgetItem] = self.__userlist_widget.selectedItems()
        self.__remove_button.setEnabled(bool(items))

    def __remove_selected(self) -> None:
        items: list[QListWidgetItem] = self.__userlist_widget.selectedItems()

        for item in items:
            self.masterlist.remove_from_ignore_list(item.text())
            self.__userlist_widget.takeItem(
                self.__userlist_widget.indexFromItem(item).row()
            )

        AppContext.get_app().user_config.save()

    def __on_text_filter_change(self, _text_filter: tuple[str, bool]) -> None:
        text_filter: str
        case_sensitive: bool
        text_filter, case_sensitive = _text_filter

        for rindex in range(self.__userlist_widget.count()):
            self.__userlist_widget.setRowHidden(
                rindex,
                not matches_filter(
                    self.__userlist_widget.item(rindex).text(),
                    text_filter,
                    case_sensitive or False,
                ),
            )
