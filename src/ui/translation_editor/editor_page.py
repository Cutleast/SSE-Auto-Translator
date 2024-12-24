"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

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

    tabs: dict[QTreeWidgetItem, EditorTab] = {}

    def __init__(self) -> None:
        super().__init__()

        self.setOrientation(Qt.Orientation.Horizontal)

        AppContext.get_app().ready_signal.connect(self.__post_init)

        self.__init_ui()

    def __init_ui(self) -> None:
        self.translations_list = QTreeWidget()
        self.translations_list.header().hide()
        self.translations_list.setColumnCount(2)
        self.translations_list.header().setStretchLastSection(False)
        self.translations_list.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.translations_list.header().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.addWidget(self.translations_list)

        self.page_widget = QStackedWidget()
        self.addWidget(self.page_widget)

        self.translations_list.currentItemChanged.connect(
            lambda cur, _: self.__set_tab_from_item(cur)
        )

    def __post_init(self) -> None:
        AppContext.get_app().database.edit_signal.connect(self.open_translation)

    def __set_tab_from_item(self, item: QTreeWidgetItem) -> None:
        """
        Sets page according to selected `item`.
        """

        if item is None:
            return

        self.page_widget.setCurrentWidget(self.tabs[item])

    def __set_tab(self, tab: EditorTab) -> None:
        """
        Sets `tab` as current visible tab.
        """

        self.translations_list.setCurrentItem(
            list(self.tabs)[list(self.tabs.values()).index(tab)]
        )

    def update(self) -> None:
        """
        Updates the displayed editor tabs.
        """

        for item, tab in self.tabs.items():
            tab.update()

            if tab.changes_pending and not item.text(0).endswith("*"):
                item.setText(0, item.text(0) + "*")
            else:
                item.setText(0, item.text(0).removesuffix("*"))

    def close_translation(self, translation: Translation, silent: bool = False) -> None:
        """
        Closes all tabs belonging to `translation`.
        """

        tabs = {
            item: tab
            for item, tab in self.tabs.items()
            if tab.translation == translation
        }

        if not len(tabs):
            return

        if any(tab.changes_pending for tab in tabs.values()) and not silent:
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

        translation_item = list(tabs.keys())[-1].parent()

        for item in tabs:
            self.tabs.pop(item)

        self.translations_list.takeTopLevelItem(
            self.translations_list.invisibleRootItem().indexOfChild(translation_item)
        )

        if self.tabs:
            self.__set_tab(list(self.tabs.values())[-1])

        AppContext.get_app().main_window.update()
        self.update()

    def open_translation(self, translation: Translation) -> None:
        """
        Opens `translation` in new tab.
        """

        set_width = not self.tabs

        # Create new tab if translation is not already open
        if not any(tab.translation == translation for tab in self.tabs.values()):
            translation_item = QTreeWidgetItem([translation.name, ""])

            translation_tab = EditorTab(translation)
            translation_tab.changes_pending_signal.connect(self.update)
            self.tabs[translation_item] = translation_tab
            self.page_widget.addWidget(translation_tab)

            close_button = QPushButton()
            close_button.setObjectName("list_close_button")
            close_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            close_button.setIcon(qta.icon("fa.close", color="#ffffff"))
            close_button.setFixedSize(26, 26)

            for plugin_name in translation.strings:
                plugin_item = QTreeWidgetItem([plugin_name, ""])
                translation_item.addChild(plugin_item)

                plugin_tab = EditorTab(translation, plugin_name)
                plugin_tab.changes_pending_signal.connect(self.update)
                self.tabs[plugin_item] = plugin_tab
                self.page_widget.addWidget(plugin_tab)

            self.translations_list.addTopLevelItem(translation_item)
            self.translations_list.setItemWidget(translation_item, 1, close_button)

            close_button.clicked.connect(lambda: self.close_translation(translation))

        self.translations_list.resizeColumnToContents(1)

        # Switch to Tab
        self.__set_tab(list(self.tabs.values())[-1])

        if set_width:
            self.setSizes([int(0.3 * self.width()), int(0.7 * self.width())])

        AppContext.get_app().main_window.update()
        self.update()
