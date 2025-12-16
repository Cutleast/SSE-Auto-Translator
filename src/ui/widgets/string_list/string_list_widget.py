"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional, TypeAlias

from cutleast_core_lib.core.utilities.reference_dict import ReferenceDict
from cutleast_core_lib.ui.utilities.tree_widget import (
    are_children_visible,
    iter_toplevel_items,
)
from cutleast_core_lib.ui.widgets.lcd_number import LCDNumber
from cutleast_core_lib.ui.widgets.search_bar import SearchBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.string import String, StringList
from core.string.string_status import StringStatus
from core.utilities import matches_filter, trim_string

from .string_list_menu import StringListMenu
from .string_list_toolbar import StringListToolbar

Strings: TypeAlias = StringList | dict[Path, StringList]
"""
A list of strings or several lists of strings.
"""


class StringListWidget(QWidget):
    """
    A widget for displaying a list of strings.
    Has its own toolbar, context menu and a search bar.
    """

    __strings: Strings
    __nested: bool
    __translation_mode: bool
    __columns: list[str]
    __string_items: ReferenceDict[String, QTreeWidgetItem]

    __state_filter: Optional[list[StringStatus]] = None
    __text_filter: Optional[tuple[str, bool]] = None

    __vlayout: QVBoxLayout
    __toolbar: StringListToolbar
    __search_bar: SearchBar
    __strings_num_label: LCDNumber
    __strings_widget: QTreeWidget
    __menu: StringListMenu

    def __init__(self, strings: Strings, translation_mode: bool = False) -> None:
        super().__init__()

        self.__strings = strings
        self.__nested = isinstance(strings, dict)
        self.__translation_mode = translation_mode
        if translation_mode:
            self.__columns = [
                self.tr("ID"),
                self.tr("Original"),
                self.tr("String"),
            ]
        else:
            self.__columns = [
                self.tr("ID"),
                self.tr("String"),
            ]

        self.__init_ui()
        self.__init_strings()

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_strings_widget()
        self.__init_context_menu()

        copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        copy_shortcut.activated.connect(self.copy_selected)

    def __init_header(self) -> None:
        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        self.__toolbar = StringListToolbar(self)
        self.__toolbar.setVisible(self.__translation_mode)
        hlayout.addWidget(self.__toolbar)

        self.__search_bar = SearchBar()
        self.__search_bar.searchChanged.connect(self.set_text_filter)
        hlayout.addWidget(self.__search_bar)

        strings_num_label = QLabel(self.tr("Strings:"))
        strings_num_label.setObjectName("h3")
        hlayout.addWidget(strings_num_label)

        self.__strings_num_label = LCDNumber()
        self.__strings_num_label.setDigitCount(6)
        hlayout.addWidget(self.__strings_num_label)

    def __init_strings_widget(self) -> None:
        self.__strings_widget = QTreeWidget()
        self.__strings_widget.setUniformRowHeights(True)
        self.__strings_widget.setAlternatingRowColors(True)
        self.__strings_widget.setSortingEnabled(True)
        self.__strings_widget.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        self.__strings_widget.header().setFirstSectionMovable(True)
        if not self.__nested:
            self.__strings_widget.setIndentation(0)
        self.__strings_widget.setSelectionMode(
            QTreeWidget.SelectionMode.ExtendedSelection
        )
        self.__strings_widget.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.__strings_widget.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.__strings_widget.itemActivated.connect(self.__show_string)
        self.__vlayout.addWidget(self.__strings_widget)

        self.__strings_widget.setHeaderLabels(self.__columns)

    def __init_context_menu(self) -> None:
        self.__menu = StringListMenu(self, self.__nested)

        self.__strings_widget.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.__strings_widget.customContextMenuRequested.connect(self.__menu.open)

    def __update(self) -> None:
        text_filter: Optional[str] = (
            self.__text_filter[0] if self.__text_filter else None
        )
        case_sensitive: Optional[bool] = (
            self.__text_filter[1] if self.__text_filter else None
        )

        for string, item in self.__string_items.items():
            string_text: str = string.display_id + string.original
            if string.string is not None:
                string_text += string.string

            item.setHidden(
                not matches_filter(string_text, text_filter, case_sensitive or False)
                or (
                    self.__state_filter is not None
                    and string.status not in self.__state_filter
                )
            )

        if self.__nested:
            for item in iter_toplevel_items(self.__strings_widget):
                item.setHidden(
                    not matches_filter(
                        item.text(0), text_filter, case_sensitive or False
                    )
                    and not are_children_visible(item)
                )

        self.__strings_num_label.display(self.get_visible_item_count())

    def __show_string(self, item: QTreeWidgetItem, column_index: int) -> None:
        column: str = self.__columns[column_index]

        if column not in [self.tr("Original"), self.tr("String")]:
            return

        strings: dict[QTreeWidgetItem, String] = {
            item: string for string, item in self.__string_items.items()
        }
        string: String = strings[item]

        # TODO: Add info box with details about the string
        dialog = QDialog(self)
        dialog.setWindowTitle(string.display_id)
        dialog.setMinimumSize(800, 500)

        vlayout = QVBoxLayout()
        dialog.setLayout(vlayout)

        textbox = QPlainTextEdit()
        textbox.setReadOnly(True)
        if column == self.tr("Original"):
            textbox.setPlainText(string.original)
        else:
            textbox.setPlainText(
                string.string if string.string is not None else string.original
            )
        textbox.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        textbox.setCursor(Qt.CursorShape.IBeamCursor)
        textbox.setFocus()
        vlayout.addWidget(textbox)

        dialog.exec()

    def __init_strings(self) -> None:
        self.__strings_widget.clear()
        self.__string_items = ReferenceDict()

        item: QTreeWidgetItem
        if self.__nested and isinstance(self.__strings, dict):
            for separator_name, strings in self.__strings.items():
                separator_item = QTreeWidgetItem([str(separator_name)])

                for string in strings:
                    item = self.__create_string_item(string)
                    separator_item.addChild(item)
                    self.__string_items[string] = item

                self.__strings_widget.addTopLevelItem(separator_item)
                separator_item.setFirstColumnSpanned(True)

        elif isinstance(self.__strings, list):
            for string in self.__strings:
                item = self.__create_string_item(string)
                self.__string_items[string] = item
                self.__strings_widget.addTopLevelItem(item)

        self.expandAll()

        if self.__translation_mode:
            self.__strings_widget.header().resizeSection(0, 500)
            self.__strings_widget.header().resizeSection(1, 400)
            self.__strings_widget.header().resizeSection(2, 400)
        else:
            self.__strings_widget.header().resizeSection(0, 650)
            self.__strings_widget.header().resizeSection(1, 650)

        if self.__nested and self.__strings_widget.topLevelItemCount() > 1:
            self.collapseAll()

        self.__search_bar.setLiveMode(len(self.__string_items) < 1000)
        self.__strings_num_label.setDigitCount(
            max((len(str(len(self.__string_items))), 4))
        )
        self.__update()

    def __create_string_item(self, string: String) -> QTreeWidgetItem:
        item = QTreeWidgetItem(
            [
                string.display_id,
                trim_string(string.original, max_length=-1),
                trim_string(
                    string.string if string.string is not None else string.original,
                    max_length=-1,
                ),
            ]
        )

        item.setToolTip(0, string.display_id)
        item.setToolTip(1, string.original)
        item.setToolTip(
            2, string.string if string.string is not None else string.original
        )

        if self.__translation_mode:
            color: Optional[QColor] = StringStatus.get_color(string.status)
            if color:
                for c in range(len(self.__columns)):
                    item.setForeground(c, color)

        item.setFont(0, QFont("Consolas"))

        return item

    @property
    def columns(self) -> list[str]:
        return self.__columns

    def set_text_filter(self, text_filter: str, case_sensitive: bool) -> None:
        """
        Sets the text filter.

        Args:
            text_filter (str): The text to filter by.
            case_sensitive (bool): Case sensitivity.
        """

        if text_filter.strip():
            self.__text_filter = (text_filter, case_sensitive)
        else:
            self.__text_filter = None
        self.__update()

    def set_state_filter(self, state_filter: list[StringStatus]) -> None:
        """
        Sets the state filter.

        Args:
            state_filter (list[StringStatus]): The states to filter by.
        """

        self.__state_filter = state_filter
        self.__update()

    def copy_selected(self, columns: Optional[list[int]] = None) -> None:
        """
        Copies current selected strings to clipboard.
        """

        clipboard_text: str = ""
        for item in self.__string_items.values():
            if not item.isSelected():
                continue

            if columns is None:
                columns = list(range(len(self.__columns)))

            for c in columns:
                clipboard_text += f"{item.toolTip(c)!r}"[1:-1] + "\t"

            clipboard_text = clipboard_text.removesuffix("\t")
            clipboard_text += "\n"

        QApplication.clipboard().setText(clipboard_text.strip())

    def expandAll(self) -> None:
        self.__strings_widget.expandAll()

    def collapseAll(self) -> None:
        self.__strings_widget.collapseAll()

    def get_selected_items(self) -> StringList:
        return [
            string for string, item in self.__string_items.items() if item.isSelected()
        ]

    def get_visible_item_count(self) -> int:
        return len(
            [item for item in self.__string_items.values() if not item.isHidden()]
        )
