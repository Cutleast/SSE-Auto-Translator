"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.ui.utilities.column_config import TreeItem
from PySide6.QtWidgets import QTreeWidgetItem

from core.string.types import String


class StringItem(TreeItem[String]):
    """
    Tree item class for strings with a custom sort order.
    """

    @override
    def __lt__(self, other: QTreeWidgetItem) -> bool:
        if not isinstance(other, StringItem):
            return super().__lt__(other)

        if self.item.status.value != other.item.status.value:
            return self.item.status.value > other.item.status.value

        return super().__lt__(other)
