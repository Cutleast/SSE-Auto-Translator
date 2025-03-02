"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Optional

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHeaderView,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
)

from app_context import AppContext
from core.database.translation import Translation

from .editor.editor_tab import EditorTab


class EditorPage(QSplitter):
    """
    Page for translation editor.
    """

    __tabs: dict[Translation, tuple[EditorTab, QTreeWidgetItem]] = {}
    """
    Mapping of translations to their tabs and the respective item in the list.
    """

    __tab_list_widget: QTreeWidget
    __page_widget: QStackedWidget

    def __init__(self) -> None:
        super().__init__()

        self.setOrientation(Qt.Orientation.Horizontal)

        AppContext.get_app().ready_signal.connect(self.__post_init)

        self.__init_ui()

    def __init_ui(self) -> None:
        self.__tab_list_widget = QTreeWidget()
        self.__tab_list_widget.header().hide()
        self.__tab_list_widget.setColumnCount(2)
        self.__tab_list_widget.header().setStretchLastSection(False)
        self.__tab_list_widget.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.__tab_list_widget.header().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.addWidget(self.__tab_list_widget)

        self.__page_widget = QStackedWidget()
        self.addWidget(self.__page_widget)

        self.__tab_list_widget.currentItemChanged.connect(
            lambda cur, _: self.__set_tab_from_item(cur)
        )

    def __post_init(self) -> None:
        AppContext.get_app().database.edit_signal.connect(self.open_translation)

    def __set_tab_from_item(self, item: Optional[QTreeWidgetItem]) -> None:
        """
        Sets page according to selected `item`.
        """

        if item is None:
            return

        tabs: dict[QTreeWidgetItem, EditorTab] = {
            item: tab for tab, item in self.__tabs.values()
        }

        # Check if item is a top level item
        tab: EditorTab
        if item.parent() is None:
            tab = tabs[item]
        else:
            tab = tabs[item.parent()]
            tab.go_to_plugin(item.text(0))

        self.__page_widget.setCurrentWidget(tab)

    def __set_tab(self, tab: EditorTab, plugin_name: Optional[str] = None) -> None:
        """
        Switches to a specified tab and goes to a specified plugin, if any.

        Args:
            tab (EditorTab): The tab to switch to.
            plugin_name (Optional[str]): The name of the plugin to go to.
        """

        item: QTreeWidgetItem = self.__tabs[tab.translation][1]
        self.__tab_list_widget.setCurrentItem(item)

        if plugin_name is not None:
            tab.go_to_plugin(plugin_name)

    @property
    def tabs(self) -> list[EditorTab]:
        """
        List of all open editor tabs.
        """

        return [tab for tab, _ in self.__tabs.values()]

    def update(self) -> None:
        """
        Updates the displayed editor tabs.
        """

        for tab, item in self.__tabs.values():
            tab.update()

            if tab.changes_pending and not item.text(0).endswith("*"):
                item.setText(0, item.text(0) + "*")
            else:
                item.setText(0, item.text(0).removesuffix("*"))

    def close_translation(self, translation: Translation, silent: bool = False) -> None:
        """
        Closes all tabs belonging to `translation`.
        """

        tab: EditorTab
        item: QTreeWidgetItem
        tab, item = self.__tabs[translation]

        if tab.changes_pending and not silent:
            message_box = QMessageBox(self)
            message_box.setWindowTitle(self.tr("Close"))
            message_box.setText(
                self.tr("Are you sure you want to close? All changes will be lost!")
            )
            message_box.setStandardButtons(
                QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(QMessageBox.StandardButton.Yes)
            message_box.button(QMessageBox.StandardButton.No).setText(self.tr("No"))
            message_box.button(QMessageBox.StandardButton.Yes).setText(self.tr("Yes"))
            choice = message_box.exec()

            if choice != QMessageBox.StandardButton.Yes:
                return

        self.__tabs.pop(translation)

        self.__tab_list_widget.takeTopLevelItem(
            self.__tab_list_widget.invisibleRootItem().indexOfChild(item)
        )

        if self.tabs:
            self.__set_tab(self.tabs[-1])

        AppContext.get_app().main_window.update()
        self.update()

    def open_translation(self, translation: Translation) -> None:
        """
        Opens `translation` in new tab.
        """

        set_width = not self.__tabs

        # Create new tab if translation is not already open
        if translation not in self.__tabs:
            translation_item = QTreeWidgetItem([translation.name])

            translation_tab = EditorTab(translation)
            translation_tab.close_signal.connect(self.close_translation)
            self.__tabs[translation] = translation_tab, translation_item
            self.__page_widget.addWidget(translation_tab)

            close_button = QPushButton()
            close_button.setObjectName("list_close_button")
            close_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            close_button.setIcon(qta.icon("fa.close", color="#ffffff"))
            close_button.setFixedSize(26, 26)

            for plugin_name in sorted(translation.strings, key=lambda p: p.lower()):
                plugin_item = QTreeWidgetItem([plugin_name])
                translation_item.addChild(plugin_item)

            self.__tab_list_widget.addTopLevelItem(translation_item)

            self.__tab_list_widget.setItemWidget(translation_item, 1, close_button)
            close_button.clicked.connect(lambda: self.close_translation(translation))

            translation_item.setExpanded(True)

        self.__tab_list_widget.resizeColumnToContents(1)

        # Switch to Tab
        self.__set_tab(self.tabs[-1])

        if set_width:
            self.setSizes(
                [
                    int(0.25 * (self.parentWidget() or self).width()),
                    int(0.75 * (self.parentWidget() or self).width()),
                ]
            )

        AppContext.get_app().main_window.update()
        self.update()
