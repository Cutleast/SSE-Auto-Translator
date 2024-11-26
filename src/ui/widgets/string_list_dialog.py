"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging

import pyperclip
import qtawesome as qta
from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QMenu,
    QPlainTextEdit,
    QToolBar,
    QTreeView,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from core.utilities import apply_dark_title_bar, trim_string
from core.utilities.localisation import Localisator
from core.utilities.string import String

from .search_bar import SearchBar


class StringListDialog(QWidget):
    """
    Dialog window for string preview.
    """

    log = logging.getLogger("StringListDialog")

    def __init__(
        self,
        app,
        name: str,
        strings: list[String] | dict[str, list[String]],
        show_translation: bool = False,
    ):
        super().__init__()

        self.app = app
        self.loc: Localisator = app.loc
        self.name = name
        self.strings = strings
        self.nested = isinstance(strings, dict)
        self.show_translation = show_translation
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setObjectName("root")
        self.setMinimumSize(1400, 800)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        apply_dark_title_bar(self)

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.tool_bar = QToolBar()
        self.tool_bar.setIconSize(QSize(32, 32))
        self.tool_bar.setFloatable(False)

        if show_translation:
            hlayout.addWidget(self.tool_bar)

        filter_menu = QMenu()

        self.filter_no_translation_required = QCheckBox(
            self.loc.editor.filter_no_translation_required, filter_menu
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
            self.loc.editor.filter_translation_complete, filter_menu
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
            self.loc.editor.filter_translation_incomplete, filter_menu
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
            self.loc.editor.filter_translation_required, filter_menu
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
            self.loc.main.filter_options,
        )
        filter_action.setMenu(filter_menu)
        filter_action.triggered.connect(
            lambda: filter_menu.exec(self.tool_bar.mapToGlobal(self.tool_bar.pos()))
        )
        self.tool_bar.addAction(filter_action)

        self.search_bar = SearchBar()
        self.search_bar.setPlaceholderText(self.loc.main.search)
        self.search_bar.cs_toggle.setToolTip(self.loc.main.case_sensitivity)
        self.search_bar.textChanged.connect(lambda text: self.update_string_list())
        hlayout.addWidget(self.search_bar)

        self.strings_widget = QTreeWidget()
        self.strings_widget.setUniformRowHeights(True)
        self.strings_widget.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )

        def on_context_menu(point: QPoint):
            menu = QMenu()

            selected_item = self.strings_widget.selectedItems()[0]

            if self.nested:
                expand_all_action = menu.addAction(self.loc.main.expand_all)
                expand_all_action.setIcon(
                    qta.icon("mdi6.arrow-expand-vertical", color="#ffffff")
                )
                expand_all_action.triggered.connect(self.strings_widget.expandAll)

                collapse_all_action = menu.addAction(self.loc.main.collapse_all)
                collapse_all_action.setIcon(
                    qta.icon("mdi6.arrow-collapse-vertical", color="#ffffff")
                )
                collapse_all_action.triggered.connect(self.strings_widget.collapseAll)

                menu.addSeparator()

            if selected_item.isFirstColumnSpanned():
                copy_plugin_name_action = menu.addAction(self.loc.main.copy_plugin_name)
                copy_plugin_name_action.setIcon(
                    qta.icon("mdi6.content-copy", color="#ffffff")
                )
                copy_plugin_name_action.triggered.connect(
                    lambda: pyperclip.copy(selected_item.text(0))
                )

            else:
                copy_menu = menu.addMenu(self.loc.main.copy)
                copy_menu.setIcon(qta.icon("mdi6.content-copy", color="#ffffff"))

                copy_all_action = copy_menu.addAction(self.loc.main.copy)
                copy_all_action.setShortcut(QKeySequence("Ctrl+C"))
                copy_all_action.setIcon(qta.icon("mdi6.content-copy", color="#ffffff"))
                copy_all_action.triggered.connect(self.copy_selected)

                headers = ["type", "form_id", "editor_id", "string"]
                if show_translation:
                    headers.insert(-1, "original")

                def get_func(c: int):
                    def func():
                        self.copy_selected(c)

                    return func

                for c, header in enumerate(headers):
                    copy_action = copy_menu.addAction(
                        getattr(self.loc.main, f"copy_{header}", f"copy_{header}")
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
        self.strings_widget.setSelectionMode(
            QTreeView.SelectionMode.ExtendedSelection
        )
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
                    self.loc.main.type,
                    self.loc.main.form_id,
                    self.loc.main.editor_id,
                    self.loc.main.original,
                    self.loc.main.string,
                ]
            )
        else:
            self.strings_widget.setHeaderLabels(
                [
                    self.loc.main.type,
                    self.loc.main.form_id,
                    self.loc.main.editor_id,
                    self.loc.main.string,
                ]
            )

        copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        copy_shortcut.activated.connect(self.copy_selected)

        self.load_strings()

    def load_strings(self):
        self.strings_widget.clear()
        self.string_items: list[tuple[String, QTreeWidgetItem]] = []

        def process_string(string: String):
            if self.show_translation:
                item = QTreeWidgetItem(
                    [
                        string.type,
                        string.form_id if string.form_id is not None else "",
                        string.editor_id if string.editor_id is not None else "",
                        trim_string(string.original_string),
                        trim_string(string.translated_string),
                    ]
                )

                item.setToolTip(0, string.type)
                if string.form_id is not None:
                    item.setToolTip(1, string.form_id)
                if string.editor_id is not None:
                    item.setToolTip(2, string.editor_id)
                item.setToolTip(3, string.original_string)
                item.setToolTip(4, string.translated_string)

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

        if self.nested:
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
        else:
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

        if len(self.string_items) > 1000:
            self.search_bar.textChanged.disconnect()
            self.search_bar.returnPressed.connect(self.update_string_list)

        self.setWindowTitle(f"{self.name} - {len(self.string_items)} String(s)")

    def update_string_list(self):
        cur_search = self.search_bar.text()
        case_sensitive = self.search_bar.cs_toggle.isChecked()

        for string, item in self.string_items:
            string_text = string.type + string.original_string
            if string.form_id is not None:
                string_text += string.form_id
            if string.editor_id is not None:
                string_text += string.editor_id
            if string.translated_string is not None:
                string_text += string.translated_string

            if case_sensitive:
                string_visible = cur_search in string_text
            else:
                string_visible = cur_search.lower() in string_text.lower()

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

    def show_string(self, item: QTreeWidgetItem, column: int):
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
        apply_dark_title_bar(dialog)

        vlayout = QVBoxLayout()
        dialog.setLayout(vlayout)

        textbox = QPlainTextEdit()
        textbox.setReadOnly(True)
        textbox.setPlainText(item.toolTip(column))
        textbox.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        textbox.setCursor(Qt.CursorShape.IBeamCursor)
        textbox.setFocus()
        vlayout.addWidget(textbox)

        dialog.exec()

    def copy_selected(self, column: int | None = None):
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
