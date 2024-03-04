"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import utilities as utils
from database import Translation
from main import MainApp

from .editor_tab import EditorTab


class TranslationEditor(qtw.QSplitter):
    """
    Page for translation editor.
    """

    tabs: list[EditorTab] = []

    def __init__(self, app: MainApp):
        super().__init__()

        self.app = app
        self.loc = app.loc
        self.mloc = app.loc.editor

        self.setOrientation(qtc.Qt.Orientation.Horizontal)

        self.translations_list = qtw.QTreeWidget()
        self.translations_list.header().hide()
        self.translations_list.setColumnCount(2)
        self.translations_list.header().setStretchLastSection(False)
        self.translations_list.header().setSectionResizeMode(
            0, qtw.QHeaderView.ResizeMode.Stretch
        )
        # self.translations_list.header().resizeSection(1, 25)
        self.translations_list.header().setSectionResizeMode(
            1, qtw.QHeaderView.ResizeMode.ResizeToContents
        )
        self.addWidget(self.translations_list)

        self.page_widget = qtw.QStackedWidget()
        self.addWidget(self.page_widget)

        self.translations_list.currentItemChanged.connect(
            lambda cur, _: self.set_tab_from_item(cur)
        )

    def set_tab_from_item(self, item: qtw.QTreeWidgetItem):
        """
        Sets page according to selected `item`.
        """

        if item is None:
            return

        # Do nothing if item belongs to a translation itself
        if item.childCount():
            return

        tab = [_tab for _tab in self.tabs if _tab.tree_item == item][0]

        self.page_widget.setCurrentWidget(tab)

    def set_tab(self, tab: EditorTab):
        """
        Sets `tab` as current visible tab.
        """

        self.translations_list.setCurrentItem(tab.tree_item)

    def close_translation(self, translation: Translation, silent: bool = False):
        """
        Closes all tabs belonging to `translation`.
        """

        tabs = [tab for tab in self.tabs if tab.translation == translation]

        if not len(tabs):
            return

        if any(tab.changes_pending for tab in tabs) and not silent:
            message_box = qtw.QMessageBox(self)
            utils.apply_dark_title_bar(message_box)
            message_box.setWindowTitle(self.loc.main.close)
            message_box.setText(self.loc.main.unsaved_close)
            message_box.setStandardButtons(
                qtw.QMessageBox.StandardButton.No | qtw.QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(qtw.QMessageBox.StandardButton.No)
            message_box.button(qtw.QMessageBox.StandardButton.No).setText(
                self.loc.main.no
            )
            message_box.button(qtw.QMessageBox.StandardButton.Yes).setText(
                self.loc.main.yes
            )
            choice = message_box.exec()

            if choice != qtw.QMessageBox.StandardButton.Yes:
                return

        translation_item = tabs[0].tree_item.parent()

        for tab in tabs:
            self.tabs.remove(tab)

        self.translations_list.takeTopLevelItem(
            self.translations_list.invisibleRootItem().indexOfChild(translation_item)
        )

        if self.tabs:
            self.set_tab(self.tabs[-1])
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
        if not any(tab.translation == translation for tab in self.tabs):
            translation_item = qtw.QTreeWidgetItem([translation.name, ""])
            close_button = qtw.QPushButton()
            close_button.setObjectName("list_close_button")
            close_button.setIcon(
                qta.icon("fa.close", color="#ffffff", color_selected="#d12525")
            )
            close_button.setFixedSize(26, 26)

            for plugin_name in translation.strings:
                plugin_item = qtw.QTreeWidgetItem([plugin_name, ""])
                translation_item.addChild(plugin_item)

                plugin_tab = EditorTab(self.app, translation, plugin_name)
                plugin_tab.tree_item = plugin_item
                plugin_tab.changes_signal.connect(
                    lambda: plugin_item.setText(0, f"{plugin_name}*")
                )
                self.tabs.append(plugin_tab)
                self.page_widget.addWidget(plugin_tab)

            self.translations_list.addTopLevelItem(translation_item)
            self.translations_list.setItemWidget(translation_item, 1, close_button)

            close_button.clicked.connect(lambda: self.close_translation(translation))

        self.translations_list.resizeColumnToContents(1)

        # Switch to Tab
        self.set_tab(self.tabs[-1])

        if set_width:
            self.setSizes([0.3 * self.width(), 0.7 * self.width()])
