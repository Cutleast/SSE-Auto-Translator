"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from PySide6.QtWidgets import (
    QDialog,
    QListWidget,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app import MainApp
from core.utilities import apply_dark_title_bar
from core.utilities.constants import AE_CC_PLUGINS, BASE_GAME_PLUGINS

from .search_bar import SearchBar


class IgnoreListDialog(QDialog):
    """
    Dialog for ignore lists.
    """

    def __init__(self, parent, app: MainApp):
        super().__init__(parent)

        self.app = app
        self.loc = app.loc
        self.mloc = app.loc.main_page

        self.setWindowTitle(self.mloc.ignore_list)
        self.resize(600, 500)
        apply_dark_title_bar(self)

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        tab_widget = QTabWidget()
        tab_widget.setObjectName("centered_tab")
        vlayout.addWidget(tab_widget)

        user_tab = QWidget()
        user_tab.setObjectName("transparent")
        tab_widget.addTab(user_tab, self.mloc.user_ignore_list)

        vlayout = QVBoxLayout()
        user_tab.setLayout(vlayout)

        remove_button = QPushButton(self.loc.main.remove_selected)
        remove_button.setDisabled(True)
        vlayout.addWidget(remove_button)

        userlist_widget = QListWidget()
        userlist_widget.setAlternatingRowColors(True)
        userlist_widget.setSelectionMode(
            userlist_widget.SelectionMode.ExtendedSelection
        )

        def on_select():
            items = userlist_widget.selectedItems()
            remove_button.setEnabled(bool(items))

        userlist_widget.itemSelectionChanged.connect(on_select)

        def remove_selected():
            items = userlist_widget.selectedItems()
            entries = [item.text() for item in items]

            for entry in entries:
                self.app.mainpage_widget.ignore_list.remove(entry)

            for item in items:
                userlist_widget.takeItem(userlist_widget.indexFromItem(item).row())

        remove_button.clicked.connect(remove_selected)

        userlist_widget.addItems(self.app.mainpage_widget.ignore_list)
        vlayout.addWidget(userlist_widget)

        search_bar = SearchBar()
        search_bar.setPlaceholderText(self.loc.main.search)
        search_bar.cs_toggle.setToolTip(self.loc.main.case_sensitivity)

        def search(text: str):
            case_sensitive = search_bar.cs_toggle.isChecked()

            for rindex in range(userlist_widget.count()):
                if case_sensitive:
                    item_visible = text in userlist_widget.item(rindex).text()
                else:
                    item_visible = (
                        text.lower() in userlist_widget.item(rindex).text().lower()
                    )

                userlist_widget.setRowHidden(rindex, not item_visible)

        search_bar.textChanged.connect(search)
        vlayout.addWidget(search_bar)

        vanilla_list_widget = QListWidget()
        vanilla_list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        vanilla_list_widget.addItems(BASE_GAME_PLUGINS + AE_CC_PLUGINS)
        tab_widget.addTab(vanilla_list_widget, self.mloc.vanilla_plugins)

        masterlist_widget = QListWidget()
        masterlist_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        masterlist_widget.addItems(
            sorted(
                plugin
                for plugin, masterlist_entry in self.app.masterlist.items()
                if masterlist_entry["type"] == "ignore"
            )
        )
        tab_widget.addTab(masterlist_widget, self.mloc.masterlist)
        tab_widget.setTabEnabled(2, bool(masterlist_widget.count()))
