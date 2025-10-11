"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from core.string import String


class StringItem(QTreeWidgetItem):
    """
    QTreeWidgetItem class for strings with a custom sort order.
    """

    __string: String

    def set_string(self, string: String) -> None:
        """
        Args:
            string (String): The string used for sorting.
        """

        self.__string = string

    @override
    def __lt__(self, other: QTreeWidgetItem) -> bool:
        if not isinstance(other, StringItem):
            return super().__lt__(other)

        tree: Optional[QTreeWidget] = self.treeWidget()
        sort_col: int = tree.sortColumn() if tree else 0

        if self.__string.status.value != other.__string.status.value:
            return self.__string.status.value > other.__string.status.value

        return self.text(sort_col) < other.text(sort_col)
