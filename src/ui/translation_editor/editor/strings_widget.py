"""
Copyright (c) Cutleast
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from core.database.string import String
from core.utilities import matches_filter, trim_string


class StringsWidget(QTreeWidget):
    """
    Class for strings widget in an editor tab.
    """

    __parent: "EditorTab"

    __string_items: dict[String, QTreeWidgetItem]
    """
    Mapping of strings to their tree items.
    """

    __name_filter: Optional[tuple[str, bool]] = None
    """
    Optional nem filter and case-sensitivity.
    """

    __state_filter: Optional[list[String.Status]] = None
    """
    Optional state filter.
    """

    def __init__(self, parent: "EditorTab", strings: list[String]) -> None:
        super().__init__(parent)

        self.__parent = parent

        self.__init_ui()
        self.__init_strings(strings)

    def __init_ui(self) -> None:
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.setUniformRowHeights(True)
        self.setIndentation(0)
        self.setSortingEnabled(True)

        self.__init_header()

    def __init_header(self) -> None:
        self.setHeaderLabels(
            [
                self.tr("Type"),
                self.tr("Form ID"),
                self.tr("Editor ID"),
                self.tr("Original"),
                self.tr("String"),
            ]
        )

        self.header().setDefaultSectionSize(200)
        self.header().setSortIndicatorClearable(True)
        self.header().setFirstSectionMovable(True)

    def __init_strings(self, strings: list[String]) -> None:
        self.__string_items = {}

        self.clear()

        for string in strings:
            item = self.__create_string_item(string)
            self.__string_items[string] = item
            self.addTopLevelItem(item)

        self.resizeColumnToContents(0)
        self.resizeColumnToContents(1)
        self.header().resizeSection(3, 500)
        self.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        self.update()

    def __create_string_item(self, string: String) -> QTreeWidgetItem:
        item = QTreeWidgetItem(
            [
                string.type,
                string.form_id if string.form_id is not None else "",
                string.editor_id if string.editor_id is not None else "",
                trim_string(string.original_string),
                trim_string(string.translated_string or string.original_string),
            ]
        )

        item.setFont(0, QFont("Consolas"))
        item.setFont(1, QFont("Consolas"))
        item.setFont(2, QFont("Consolas"))

        return item

    def update(self) -> None:
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
            item.setText(3, trim_string(string.original_string))
            item.setText(
                4, trim_string(string.translated_string or string.original_string)
            )

            item.setHidden(
                (
                    self.__state_filter is not None
                    and string.status not in self.__state_filter
                )
                or not matches_filter(
                    # TODO: Make filtering by other stuff possible
                    string.original_string,
                    name_filter,
                    case_sensitive or False,
                )
            )

            for c in range(5):
                item.setForeground(
                    c, String.Status.get_color(string.status) or Qt.GlobalColor.white
                )

        if self.selectedItems():
            self.scrollToItem(
                self.selectedItems()[0], QTreeWidget.ScrollHint.PositionAtCenter
            )

    def set_name_filter(self, name_filter: tuple[str, bool]) -> None:
        """
        Sets the name filter.

        Args:
            name_filter (tuple[str, bool]): The name to filter by and case-sensitivity.
        """

        self.__name_filter = name_filter if name_filter[0].strip() else None
        self.update()

    def set_state_filter(self, state_filter: list[String.Status]) -> None:
        """
        Sets the state filter.

        Args:
            state_filter (list[String.Status]): The states to filter by.
        """

        self.__state_filter = state_filter
        self.update()

    def get_selected_strings(self) -> list[String]:
        """
        Gets the selected strings.

        Returns:
            list[String]: The selected strings.
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

    def get_visible_strings(self) -> list[String]:
        """
        Returns a list of strings that are visible with current filter.

        Returns:
            list[String]: The visible strings.
        """

        return [
            string
            for string, item in sorted(
                self.__string_items.items(),
                key=lambda i: self.indexOfTopLevelItem(i[1]),
            )
            if not item.isHidden()
        ]

    def get_index_of_string(self, string: String) -> int:
        """
        Gets the index of a string in the list.

        Args:
            string (String): The string to get the index of.

        Returns:
            int: The index
        """

        return self.indexOfTopLevelItem(self.__string_items[string])


if __name__ == "__main__":
    from .editor_tab import EditorTab
