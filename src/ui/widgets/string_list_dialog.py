"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
from typing import Callable, Optional

import pyperclip
import qtawesome as qta
from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QPlainTextEdit,
    QToolBar,
    QTreeView,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from core.database.string import String
from core.utilities import matches_filter, trim_string

from .menu import Menu
from .search_bar import SearchBar


class StringListDialog(QWidget):
    """
    Dialog window for string preview.
    """

    log = logging.getLogger("StringListDialog")

    def __init__(
        self,
        name: str,
        strings: list[String] | dict[str, list[String]],
        show_translation: bool = False,
    ):
        super().__init__()

        self.name = name
        self.strings = strings
        self.nested = isinstance(strings, dict)
        self.show_translation = show_translation
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setObjectName("root")
        self.setMinimumSize(1400, 800)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.tool_bar = QToolBar()
        self.tool_bar.setIconSize(QSize(32, 32))
        self.tool_bar.setFloatable(False)

        if show_translation:
            hlayout.addWidget(self.tool_bar)

        filter_menu = Menu()

        self.filter_no_translation_required = QCheckBox(
            self.tr("Show Strings that require no Translation"), filter_menu
        )
        self.filter_no_translation_required.setObjectName("menu_checkbox")
        self.filter_no_translation_required.setChecked(True)
        self.filter_no_translation_required.stateChanged.connect(
            lambda _: self.update_string_list()
        )
        widget_action = QWidgetAction(filter_menu)
        widget_action.setDefaultWidget(self.filter_no_translation_required)
        filter_menu.addAction(widget_action)

        self.filter_translation_complete = QCheckBox(
            self.tr("Show Strings with complete Translation"), filter_menu
        )
        self.filter_translation_complete.setObjectName("menu_checkbox")
        self.filter_translation_complete.setChecked(True)
        self.filter_translation_complete.stateChanged.connect(
            lambda _: self.update_string_list()
        )
        widget_action = QWidgetAction(filter_menu)
        widget_action.setDefaultWidget(self.filter_translation_complete)
        filter_menu.addAction(widget_action)

        self.filter_translation_incomplete = QCheckBox(
            self.tr("Show Strings with incomplete Translation"), filter_menu
        )
        self.filter_translation_incomplete.setObjectName("menu_checkbox")
        self.filter_translation_incomplete.setChecked(True)
        self.filter_translation_incomplete.stateChanged.connect(
            lambda _: self.update_string_list()
        )
        widget_action = QWidgetAction(filter_menu)
        widget_action.setDefaultWidget(self.filter_translation_incomplete)
        filter_menu.addAction(widget_action)

        self.filter_translation_required = QCheckBox(
            self.tr("Show Strings that require a Translation"), filter_menu
        )
        self.filter_translation_required.setObjectName("menu_checkbox")
        self.filter_translation_required.setChecked(True)
        self.filter_translation_required.stateChanged.connect(
            lambda _: self.update_string_list()
        )
        widget_action = QWidgetAction(filter_menu)
        widget_action.setDefaultWidget(self.filter_translation_required)
        filter_menu.addAction(widget_action)

        filter_action = self.tool_bar.addAction(
            qta.icon("mdi6.filter", color="#ffffff"),
            self.tr("Filter Options"),
        )
        filter_action.setMenu(filter_menu)
        filter_action.triggered.connect(
            lambda: filter_menu.exec(self.tool_bar.mapToGlobal(self.tool_bar.pos()))
        )
        self.tool_bar.addAction(filter_action)

        self.search_bar = SearchBar()
        self.search_bar.setPlaceholderText(self.tr("Search..."))
        self.search_bar.searchChanged.connect(self.update_string_list)
        hlayout.addWidget(self.search_bar)

        self.strings_widget = QTreeWidget()
        self.strings_widget.setUniformRowHeights(True)
        self.strings_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # TODO: Refactor this
        def on_context_menu(point: QPoint) -> None:
            menu = Menu()

            selected_item = self.strings_widget.selectedItems()[0]

            if self.nested:
                expand_all_action = menu.addAction(self.tr("Expand all"))
                expand_all_action.setIcon(
                    qta.icon("mdi6.arrow-expand-vertical", color="#ffffff")
                )
                expand_all_action.triggered.connect(self.strings_widget.expandAll)

                collapse_all_action = menu.addAction(self.tr("Collapse all"))
                collapse_all_action.setIcon(
                    qta.icon("mdi6.arrow-collapse-vertical", color="#ffffff")
                )
                collapse_all_action.triggered.connect(self.strings_widget.collapseAll)

                menu.addSeparator()

            if selected_item.isFirstColumnSpanned():
                copy_plugin_name_action = menu.addAction(self.tr("Copy plugin name"))
                copy_plugin_name_action.setIcon(
                    qta.icon("mdi6.content-copy", color="#ffffff")
                )
                copy_plugin_name_action.triggered.connect(
                    lambda: pyperclip.copy(selected_item.text(0))
                )

            else:
                copy_menu = menu.addMenu(self.tr("Copy"))
                copy_menu.setIcon(qta.icon("mdi6.content-copy", color="#ffffff"))

                copy_all_action = copy_menu.addAction(self.tr("Copy"))
                copy_all_action.setShortcut(QKeySequence("Ctrl+C"))
                copy_all_action.setIcon(qta.icon("mdi6.content-copy", color="#ffffff"))
                copy_all_action.triggered.connect(self.copy_selected)

                headers = [
                    self.tr("Type"),
                    self.tr("Form ID"),
                    self.tr("Editor ID"),
                    self.tr("String"),
                ]
                if show_translation:
                    headers.insert(-1, self.tr("Original"))

                def get_func(c: int) -> Callable[[], None]:
                    def func() -> None:
                        self.copy_selected(c)

                    return func

                for c, header in enumerate(headers):
                    copy_action = copy_menu.addAction(
                        self.tr("Copy {}").format(header),
                    )
                    copy_action.setIcon(qta.icon("mdi6.content-copy", color="#ffffff"))
                    copy_action.triggered.connect(get_func(c))

            menu.exec(self.strings_widget.mapToGlobal(point))

        self.strings_widget.customContextMenuRequested.connect(on_context_menu)
        self.strings_widget.setAlternatingRowColors(True)
        self.strings_widget.setSortingEnabled(True)
        self.strings_widget.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        self.strings_widget.header().setFirstSectionMovable(True)
        if not self.nested:
            self.strings_widget.setIndentation(0)
        self.strings_widget.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        self.strings_widget.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.strings_widget.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.strings_widget.itemActivated.connect(self.show_string)
        vlayout.addWidget(self.strings_widget)

        # Tree view model for strings
        if show_translation:
            self.strings_widget.setHeaderLabels(
                [
                    self.tr("Type"),
                    self.tr("Form ID"),
                    self.tr("Editor ID"),
                    self.tr("Original"),
                    self.tr("String"),
                ]
            )
        else:
            self.strings_widget.setHeaderLabels(
                [
                    self.tr("Type"),
                    self.tr("Form ID"),
                    self.tr("Editor ID"),
                    self.tr("String"),
                ]
            )

        copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        copy_shortcut.activated.connect(self.copy_selected)

        self.load_strings()

    def load_strings(self) -> None:
        self.strings_widget.clear()
        self.string_items: list[tuple[String, QTreeWidgetItem]] = []

        def process_string(string: String) -> QTreeWidgetItem:
            if self.show_translation:
                item = QTreeWidgetItem(
                    [
                        string.type,
                        string.form_id if string.form_id is not None else "",
                        string.editor_id if string.editor_id is not None else "",
                        trim_string(string.original_string),
                        trim_string(string.translated_string or string.original_string),
                    ]
                )

                item.setToolTip(0, string.type)
                if string.form_id is not None:
                    item.setToolTip(1, string.form_id)
                if string.editor_id is not None:
                    item.setToolTip(2, string.editor_id)
                item.setToolTip(3, string.original_string)
                item.setToolTip(4, string.translated_string or string.original_string)

                color = string.Status.get_color(string.status)
                if color:
                    for c in range(5):
                        item.setForeground(c, color)
            else:
                item = QTreeWidgetItem(
                    [
                        string.type,
                        string.form_id if string.form_id is not None else "",
                        string.editor_id if string.editor_id is not None else "",
                        trim_string(string.original_string),
                    ]
                )

                item.setToolTip(0, string.type)
                if string.form_id is not None:
                    item.setToolTip(1, string.form_id)
                if string.editor_id is not None:
                    item.setToolTip(2, string.editor_id)
                item.setToolTip(3, string.original_string)

            item.setFont(0, QFont("Consolas"))
            item.setFont(1, QFont("Consolas"))
            item.setFont(2, QFont("Consolas"))

            return item

        if self.nested and isinstance(self.strings, dict):
            for section, strings in self.strings.items():
                section_item = QTreeWidgetItem([section])

                for string in strings:
                    item = process_string(string)

                    self.string_items.append((string, item))
                    section_item.addChild(item)

                self.strings_widget.addTopLevelItem(section_item)
                section_item.setFirstColumnSpanned(True)

            if len(self.strings) == 1:
                self.strings_widget.topLevelItem(0).setExpanded(True)
        elif isinstance(self.strings, list):
            for string in self.strings:
                item = process_string(string)

                self.string_items.append((string, item))
                self.strings_widget.addTopLevelItem(item)

        self.strings_widget.header().resizeSection(0, 130)
        self.strings_widget.resizeColumnToContents(1)
        self.strings_widget.header().resizeSection(2, 200)

        if self.show_translation:
            self.strings_widget.header().resizeSection(3, 300)
            self.strings_widget.header().resizeSection(4, 300)
        else:
            self.strings_widget.header().resizeSection(3, 600)

        # if len(self.string_items) > 1000:
        #     self.search_bar.textChanged.disconnect()
        #     self.search_bar.returnPressed.connect(self.update_string_list)
        self.search_bar.setLiveMode(len(self.string_items) > 1000)

        self.setWindowTitle(f"{self.name} - {len(self.string_items)} String(s)")

    def update_string_list(
        self, name_filter: Optional[tuple[str, bool]] = None
    ) -> None:
        cur_search: str = (
            name_filter[0] if name_filter is not None else self.search_bar.text()
        )
        case_sensitive: bool = (
            name_filter[1]
            if name_filter is not None
            else self.search_bar.getCaseSensitivity()
        )

        for string, item in self.string_items:
            string_text = string.type + string.original_string
            if string.form_id is not None:
                string_text += string.form_id
            if string.editor_id is not None:
                string_text += string.editor_id
            if string.translated_string is not None:
                string_text += string.translated_string

            string_visible = matches_filter(string_text, cur_search, case_sensitive)

            if string_visible:
                match string.status:
                    case string.Status.NoTranslationRequired:
                        string_visible = self.filter_no_translation_required.isChecked()
                    case string.Status.TranslationComplete:
                        string_visible = self.filter_translation_complete.isChecked()
                    case string.Status.TranslationIncomplete:
                        string_visible = self.filter_translation_incomplete.isChecked()
                    case string.Status.TranslationRequired:
                        string_visible = self.filter_translation_required.isChecked()

            item.setHidden(not string_visible)

        # Update root items
        if self.nested:
            for rindex in range(self.strings_widget.topLevelItemCount()):
                root_item = self.strings_widget.topLevelItem(rindex)
                visible = False

                for cindex in range(root_item.childCount()):
                    child_item = root_item.child(cindex)

                    if not child_item.isHidden():
                        visible = True

                root_item.setHidden(not visible)

        if self.strings_widget.selectedItems():
            self.strings_widget.scrollToItem(
                self.strings_widget.selectedItems()[0],
                QTreeWidget.ScrollHint.PositionAtCenter,
            )

    def show_string(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Shows `string` in a separate text box window.
        """

        if column < 3:
            return

        dialog = QDialog(self)
        type = item.text(0)
        form_id = item.text(1)
        editor_id = item.text(2)
        if editor_id:
            dialog.setWindowTitle(f"{editor_id} ({type})")
        else:
            dialog.setWindowTitle(f"{form_id} ({type})")
        dialog.setMinimumSize(800, 500)

        vlayout = QVBoxLayout()
        dialog.setLayout(vlayout)

        textbox = QPlainTextEdit()
        textbox.setReadOnly(True)
        textbox.setPlainText(item.toolTip(column))
        textbox.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        textbox.setCursor(Qt.CursorShape.IBeamCursor)
        textbox.setFocus()
        vlayout.addWidget(textbox)

        dialog.exec()

    def copy_selected(self, column: int | None = None) -> None:
        """
        Copies current selected strings to clipboard.
        """

        selected_items = self.strings_widget.selectedItems()

        clipboard_text = ""
        for item in selected_items:
            if item.childCount():  # Skip items with children (sections if nested)
                continue

            if column is None:
                for c in range(self.strings_widget.columnCount()):
                    clipboard_text += f"{item.toolTip(c)!r}"[1:-1] + "\t"
            else:
                clipboard_text += item.toolTip(column)

            clipboard_text = clipboard_text.removesuffix("\t")
            clipboard_text += "\n"

        pyperclip.copy(clipboard_text.strip())
