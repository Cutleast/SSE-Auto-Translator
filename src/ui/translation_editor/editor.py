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

from app import MainApp
from core.database.translation import Translation
from core.utilities import apply_dark_title_bar

from .editor_tab import EditorTab


class TranslationEditor(QSplitter):
    """
    Page for translation editor.
    """

    tabs: dict[QTreeWidgetItem, EditorTab] = {}

    def __init__(self, app: MainApp):
        super().__init__()

        self.app = app
        self.loc = app.loc
        self.mloc = app.loc.editor

        self.setOrientation(Qt.Orientation.Horizontal)

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
            lambda cur, _: self.set_tab_from_item(cur)
        )

    def set_tab_from_item(self, item: QTreeWidgetItem):
        """
        Sets page according to selected `item`.
        """

        if item is None:
            return

        self.page_widget.setCurrentWidget(self.tabs[item])

    def get_current_tab(self) -> EditorTab | None:
        """
        Returns current `tab` that is open.
        """

        if self.tabs:
            return self.page_widget.currentWidget()

    def set_tab(self, tab: EditorTab):
        """
        Sets `tab` as current visible tab.
        """

        self.translations_list.setCurrentItem(list(self.tabs)[list(self.tabs.values()).index(tab)])

    def close_translation(self, translation: Translation, silent: bool = False):
        """
        Closes all tabs belonging to `translation`.
        """

        tabs = {
            item: tab
            for item, tab in self.tabs.items() if tab.translation == translation
        }

        if not len(tabs):
            return

        if any(tab.changes_pending for tab in tabs.values()) and not silent:
            message_box = QMessageBox(self)
            apply_dark_title_bar(message_box)
            message_box.setWindowTitle(self.loc.main.close)
            message_box.setText(self.loc.main.unsaved_close)
            message_box.setStandardButtons(
                QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(QMessageBox.StandardButton.Yes)
            message_box.button(QMessageBox.StandardButton.No).setText(
                self.loc.main.no
            )
            message_box.button(QMessageBox.StandardButton.Yes).setText(
                self.loc.main.yes
            )
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
            self.set_tab(list(self.tabs.values())[-1])
        else:
            self.app.tab_widget.setCurrentIndex(0)
            self.app.tab_widget.setTabEnabled(1, False)

    def open_translation(self, translation: Translation):
        """
        Opens `translation` in new tab.
        """

        self.app.tab_widget.setTabEnabled(1, True)

        set_width = not self.tabs

        # Create new tab if translation is not already open
        if not any(tab.translation == translation for tab in self.tabs.values()):
            translation_item = QTreeWidgetItem([translation.name, ""])
            
            translation_tab = EditorTab(self.app, translation)
            translation_tab.changes_signal.connect(
                lambda: translation_item.setText(0, f"{translation.name}*")
            )
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

                plugin_tab = EditorTab(self.app, translation, plugin_name)
                plugin_tab.changes_signal.connect(
                    lambda: plugin_item.setText(0, f"{plugin_name}*")
                )
                self.tabs[plugin_item] = plugin_tab
                self.page_widget.addWidget(plugin_tab)

            self.translations_list.addTopLevelItem(translation_item)
            self.translations_list.setItemWidget(translation_item, 1, close_button)

            close_button.clicked.connect(lambda: self.close_translation(translation))

        self.translations_list.resizeColumnToContents(1)

        # Switch to Tab
        self.set_tab(list(self.tabs.values())[-1])

        if set_width:
            self.setSizes([0.3 * self.width(), 0.7 * self.width()])
