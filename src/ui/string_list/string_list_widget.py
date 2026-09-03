"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional, TypeAlias

from cutleast_core_lib.core.utilities.filter import matches_filter
from cutleast_core_lib.core.utilities.pydantic_utils import ImmutableValue
from cutleast_core_lib.core.utilities.reference_dict import ReferenceDict
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.theme.models.theme import Theme
from cutleast_core_lib.ui.utilities.column_config import TreeItem
from cutleast_core_lib.ui.utilities.state_manager import WidgetStateManager
from cutleast_core_lib.ui.utilities.tree_widget import (
    are_children_visible,
    iter_toplevel_items,
)
from cutleast_core_lib.ui.widgets.search_bar import SearchBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QPlainTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.string.string_status import StringStatus
from core.string.types import String, StringList
from ui.string_list.columns import StringsColumns

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
    __string_items: ReferenceDict[String, TreeItem[String]]
    __rendered_columns: frozenset[StringsColumns]

    __state_filter: Optional[list[StringStatus]] = None
    __text_filter: Optional[tuple[str, bool]] = None

    __vlayout: QVBoxLayout
    __toolbar: StringListToolbar
    __search_bar: SearchBar
    __strings_num_label: QLabel
    __strings_widget: QTreeWidget
    __menu: StringListMenu

    __copy_shortcut: QShortcut

    def __init__(self, strings: Strings, translation_mode: bool = False) -> None:
        """
        Args:
            strings (Strings): The strings to display.
            translation_mode (bool, optional):
                If the strings belong to a translation. Defaults to False.
        """

        super().__init__()

        self.__strings = strings
        self.__nested = isinstance(strings, dict)
        self.__translation_mode = translation_mode
        self.__rendered_columns = (
            frozenset(StringsColumns)
            if translation_mode
            else frozenset((StringsColumns.Id, StringsColumns.Original))
        )

        self.__init_ui()

        self.__strings_widget.setColumnHidden(
            StringsColumns.Status.index, not translation_mode
        )
        self.__strings_widget.setColumnHidden(
            StringsColumns.Translation.index, not translation_mode
        )

        self.__toolbar.filter_changed.connect(self.__set_state_filter)
        self.__search_bar.searchChanged.connect(self.__set_text_filter)
        self.__strings_widget.itemActivated.connect(self.__show_string)
        self.__strings_widget.customContextMenuRequested.connect(
            lambda *_: self.__menu.open(len(self.get_selected_items()))
        )
        self.__copy_shortcut.activated.connect(self.__copy_selected)

        self.__menu.expand_all_clicked.connect(self.__strings_widget.expandAll)
        self.__menu.collapse_all_clicked.connect(self.__strings_widget.collapseAll)
        self.__menu.copy_selected_requested.connect(self.__copy_selected)

        self.__init_strings()

        self.__strings_widget.setSortingEnabled(True)

        ThemeManager.get().theme_changed.connect(self.__on_theme_changed)

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_strings_widget()
        self.__init_context_menu()

        self.__copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)

    def __init_header(self) -> None:
        self.__toolbar = StringListToolbar()
        self.__toolbar.set_filter_action_visible(self.__translation_mode)
        self.__vlayout.addWidget(self.__toolbar)

        self.__search_bar = SearchBar()
        self.__toolbar.addWidget(self.__search_bar)

        self.__toolbar.addSeparator()

        strings_num_label = QLabel(self.tr("Strings:"))
        strings_num_label.setProperty("subtitle", True)
        self.__toolbar.addWidget(strings_num_label)

        self.__strings_num_label = QLabel()
        self.__strings_num_label.setProperty("subtitle", True)
        self.__toolbar.addWidget(self.__strings_num_label)

    def __init_strings_widget(self) -> None:
        self.__strings_widget = QTreeWidget()
        StringsColumns.apply_to_tree_widget(self.__strings_widget)

        self.__strings_widget.setSelectionMode(
            QTreeWidget.SelectionMode.ExtendedSelection
        )
        self.__strings_widget.setUniformRowHeights(True)
        self.__strings_widget.header().setFirstSectionMovable(True)
        if not self.__nested:
            self.__strings_widget.setIndentation(0)

        self.__vlayout.addWidget(self.__strings_widget)

        WidgetStateManager.get().register_state(
            "string_list_widget_header", self.__strings_widget.header()
        )

    def __init_context_menu(self) -> None:
        self.__menu = StringListMenu(
            [c.value.get_title() for c in StringsColumns], self.__nested
        )

        self.__strings_widget.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )

    def __update(self) -> None:
        name_filter: Optional[str] = (
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
                (
                    self.__state_filter is not None
                    and string.status not in self.__state_filter
                )
                or not matches_filter(string_text, name_filter, case_sensitive or False)
            )

        for item in iter_toplevel_items(self.__strings_widget):
            if (
                not isinstance(item, TreeItem)
                or not isinstance(item.item, ImmutableValue)
                or not isinstance(item.item.value, Path)
            ):
                continue

            item.setHidden(
                not are_children_visible(item)
                and (
                    not matches_filter(
                        str(item.item.value), name_filter, case_sensitive or False
                    )
                    or self.__state_filter is not None
                )
            )

        self.__strings_num_label.setText(str(self.get_visible_item_count()))

    def __show_string(self, item: QTreeWidgetItem, column_index: int) -> None:
        if column_index not in [
            StringsColumns.Original.index,
            StringsColumns.Translation.index,
        ]:
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
        if column_index == StringsColumns.Original.index:
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
                separator_item = TreeItem(
                    ImmutableValue(separator_name),
                    StringsColumns,
                    rendered_columns=self.__rendered_columns,
                )

                for string in strings:
                    item = TreeItem(
                        string,
                        StringsColumns,
                        rendered_columns=self.__rendered_columns,
                    )
                    separator_item.addChild(item)
                    self.__string_items[string] = item

                self.__strings_widget.addTopLevelItem(separator_item)
                separator_item.setFirstColumnSpanned(True)

        elif isinstance(self.__strings, list):
            for string in self.__strings:
                item = TreeItem(
                    string,
                    StringsColumns,
                    rendered_columns=self.__rendered_columns,
                )
                self.__string_items[string] = item
                self.__strings_widget.addTopLevelItem(item)

        self.__strings_widget.expandAll()

        if self.__nested and self.__strings_widget.topLevelItemCount() > 1:
            self.__strings_widget.collapseAll()

        self.__update()

    def __set_text_filter(self, text_filter: str, case_sensitive: bool) -> None:
        if text_filter.strip():
            self.__text_filter = (text_filter, case_sensitive)
        else:
            self.__text_filter = None
        self.__update()

    def __set_state_filter(self, state_filter: list[StringStatus]) -> None:
        self.__state_filter = state_filter
        self.__update()

    def __copy_selected(self, col_idxs: Optional[list[int]] = None) -> None:
        clipboard_text: str = ""
        for item in self.__string_items.values():
            if not item.isSelected():
                continue

            columns: list[StringsColumns] = [
                c for c in StringsColumns if col_idxs is None or c.index in col_idxs
            ]

            for c in columns:
                clipboard_text += c.value.get_copy_text(item.item) + "\t"

            clipboard_text = clipboard_text.removesuffix("\t")
            clipboard_text += "\n"

        QApplication.clipboard().setText(clipboard_text.strip())

    def __on_theme_changed(self, theme: Theme) -> None:
        for item in self.__string_items.values():
            item.update()

    def get_visible_item_count(self) -> int:
        """
        Returns:
            int: The number of currently visible strings.
        """

        return len(
            [item for item in self.__string_items.values() if not item.isHidden()]
        )

    def get_selected_items(self) -> StringList:
        """
        Returns:
            StringList: A list of currently selected strings.
        """

        return [
            string for string, item in self.__string_items.items() if item.isSelected()
        ]
