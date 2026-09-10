"""
Copyright (c) Cutleast
"""

from typing import Optional

from cutleast_core_lib.core.utilities.filter import matches_filter
from cutleast_core_lib.ui.widgets.search_bar import SearchBar
from cutleast_core_lib.ui.widgets.tab_widget import TabWidget
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.config.user_config import UserConfig
from core.masterlist.masterlist import Masterlist
from core.masterlist.masterlist_entry import MasterlistEntry
from core.utilities.constants import AE_CC_PLUGINS, BASE_GAME_PLUGINS


class IgnoreListDialog(QDialog):
    """
    Dialog for ignore lists.
    """

    __masterlist: Masterlist
    __user_config: UserConfig

    __userlist_widget: QListWidget
    __remove_button: QPushButton

    def __init__(
        self,
        masterlist: Masterlist,
        user_config: UserConfig,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Args:
            masterlist (Masterlist): The loaded masterlist.
            user_config (UserConfig): The user configuration.
            parent (Optional[QWidget], optional):
                Optional parent widget. Defaults to None.
        """

        super().__init__(parent)

        self.__masterlist = masterlist
        self.__user_config = user_config

        self.setWindowTitle(self.tr("Ignore list"))
        self.resize(600, 500)

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        tab_widget = TabWidget()
        tab_widget.setTabBarAlignment(Qt.AlignmentFlag.AlignHCenter)
        vlayout.addWidget(tab_widget)

        user_tab = QWidget()
        tab_widget.addTab(user_tab, self.tr("User ignore list"))

        vlayout = QVBoxLayout()
        vlayout.setContentsMargins(0, 0, 0, 0)
        user_tab.setLayout(vlayout)

        self.__remove_button = QPushButton(
            self.tr("Remove selected mod file(s) from list")
        )
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
        self.__userlist_widget.addItems(self.__masterlist.user_ignore_list)
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
                filename
                for filename, masterlist_entry in self.__masterlist.entries.items()
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
            self.__masterlist.remove_from_ignore_list(item.text())
            self.__userlist_widget.takeItem(
                self.__userlist_widget.indexFromItem(item).row()
            )

        self.__user_config.save()

    def __on_text_filter_change(self, text_filter: str, case_sensitive: bool) -> None:
        for rindex in range(self.__userlist_widget.count()):
            self.__userlist_widget.setRowHidden(
                rindex,
                not matches_filter(
                    self.__userlist_widget.item(rindex).text(),
                    text_filter,
                    case_sensitive,
                ),
            )
