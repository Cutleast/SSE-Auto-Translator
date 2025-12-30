"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional, override

from cutleast_core_lib.core.utilities.reference_dict import ReferenceDict
from cutleast_core_lib.ui.utilities.tree_widget import (
    are_children_visible,
    iter_children,
    iter_toplevel_items,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from core.string.string_status import StringStatus
from core.string.types import String, StringList
from core.utilities import matches_filter, trim_string

from .string_item import StringItem


class StringsWidget(QTreeWidget):
    """
    Class for strings widget in an editor tab.
    """

    __string_items: ReferenceDict[String, StringItem]
    """
    Mapping of strings to their tree items.

    A `ReferenceDict` is required here because the Strings are used as the keys
    but they're mutable and their hash may change.
    """

    __modfile_items: dict[Path, QTreeWidgetItem]
    """
    Mapping of mod file names to their tree items.
    """

    __name_filter: Optional[tuple[str, bool]] = None
    """
    Optional name filter and case-sensitivity.
    """

    __state_filter: Optional[list[StringStatus]] = None
    """
    Optional state filter.
    """

    def __init__(self, strings: dict[Path, StringList]) -> None:
        super().__init__()

        self.__init_ui()
        self.__init_strings(strings)

    def __init_ui(self) -> None:
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.setUniformRowHeights(True)
        self.setSortingEnabled(True)

        self.__init_header()

    def __init_header(self) -> None:
        self.setHeaderLabels(
            [
                self.tr("ID"),
                self.tr("Original"),
                self.tr("String"),
            ]
        )

        self.header().setDefaultSectionSize(200)
        self.header().setSortIndicatorClearable(True)

    def __init_strings(self, strings: dict[Path, StringList]) -> None:
        self.__string_items = ReferenceDict()
        self.__modfile_items = {}

        self.clear()

        for modfile, modfile_strings in sorted(
            strings.items(), key=lambda p: p[0].name.lower()
        ):
            modfile_item = QTreeWidgetItem([str(modfile)])
            self.__modfile_items[modfile] = modfile_item

            for string in modfile_strings:
                if string in self.__string_items:
                    raise ValueError(f"Duplicate string: {string}")

                item = self.__create_string_item(string)
                self.__string_items[string] = item
                modfile_item.addChild(item)

            self.addTopLevelItem(modfile_item)
            modfile_item.setFirstColumnSpanned(True)

        self.expandAll()
        self.header().resizeSection(0, 500)
        self.header().resizeSection(1, 400)
        self.header().resizeSection(2, 400)
        self.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.update()

    def __create_string_item(self, string: String) -> StringItem:
        item = StringItem(
            [
                string.display_id,
                trim_string(string.original),
                trim_string(
                    string.string if string.string is not None else string.original
                ),
            ]
        )
        item.set_string(string)

        item.setFont(0, QFont("Consolas"))

        return item

    def __get_items(self, only_visible: bool = False) -> list[QTreeWidgetItem]:
        return [
            string_item
            for modfile_item in iter_toplevel_items(self)
            for string_item in iter_children(modfile_item)
            if not only_visible or not string_item.isHidden()
        ]

    @override
    def update(self) -> None:  # type: ignore
        """
        Updates the strings widget.
        """

        name_filter: Optional[str] = (
            self.__name_filter[0] if self.__name_filter else None
        )
        case_sensitive: Optional[bool] = (
            self.__name_filter[1] if self.__name_filter else None
        )

        for string, item in self.__string_items.items():
            item.setText(1, trim_string(string.original))
            item.setText(
                2,
                trim_string(
                    string.string if string.string is not None else string.original
                ),
            )

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

            for c in range(5):
                item.setForeground(
                    c,
                    StringStatus.get_color(string.status) or Qt.GlobalColor.white,
                )

        for modfile, modfile_item in self.__modfile_items.items():
            modfile_item.setHidden(
                not are_children_visible(modfile_item)
                and (
                    not matches_filter(
                        str(modfile), name_filter, case_sensitive or False
                    )
                    or self.__state_filter is not None
                )
            )

        if self.currentItem():
            self.scrollToItem(
                self.currentItem(), QTreeWidget.ScrollHint.PositionAtCenter
            )

    def go_to_modfile(self, modfile: Path) -> None:
        """
        Selects and scrolls to a specified mod file item.

        Args:
            modfile (Path):
                The path of the mod file, relative to the game's "Data" folder.
        """

        item: QTreeWidgetItem = self.__modfile_items[modfile]
        item.setSelected(True)
        self.setCurrentItem(item)
        self.scrollToItem(item, QTreeWidget.ScrollHint.PositionAtTop)

    def set_name_filter(self, name_filter: str, case_sensitive: bool) -> None:
        """
        Sets the name filter.

        Args:
            name_filter (str): The name to filter by.
            case_sensitive (bool): Case sensitivity.
        """

        if name_filter.strip():
            self.__name_filter = (name_filter, case_sensitive)
        else:
            self.__name_filter = None
        self.update()

    def set_state_filter(self, state_filter: list[StringStatus]) -> None:
        """
        Sets the state filter.

        Args:
            state_filter (list[StringStatus]): The states to filter by.
        """

        self.__state_filter = state_filter
        self.update()

    def get_selected_strings(self) -> StringList:
        """
        Gets the selected strings.

        Returns:
            StringList: The selected strings.
        """

        return [
            string for string, item in self.__string_items.items() if item.isSelected()
        ]

    def get_current_string(self) -> Optional[String]:
        """
        Gets the currently selected string.

        Returns:
            Optional[String]: The current string
        """

        items: dict[QTreeWidgetItem, String] = {
            item: string for string, item in self.__string_items.items()
        }

        return items.get(self.currentItem())

    def get_visible_string_count(self) -> int:
        """
        Gets number of visible strings.

        Returns:
            int: Number of visible strings
        """

        return len(self.__get_items(only_visible=True))

    def get_index_of_string(self, string: String, only_visible: bool = False) -> int:
        """
        Gets the index of a string in the list.

        Args:
            string (String): The string to get the index of.
            only_visible (bool, optional):
                Whether to get the index within the visible strings.

        Returns:
            int: The index
        """

        return self.__get_items(only_visible).index(self.__string_items[string])

    def get_string_from_index(
        self, index: int, only_visible: bool = False
    ) -> Optional[String]:
        """
        Gets a string from an index.

        Args:
            index (int): The index.
            only_visible (bool, optional):
                Whether to get the string within the visible strings. Defaults to False.

        Returns:
            Optional[String]: The string or None if not found.
        """

        items: list[QTreeWidgetItem] = self.__get_items(only_visible)

        if index >= len(items):
            return None

        string_items: dict[QTreeWidgetItem, String] = {
            item: string for string, item in self.__string_items.items()
        }

        return string_items[items[index]]
