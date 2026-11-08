"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.ui.utilities.column_config import TreeItem
from PySide6.QtWidgets import QTreeWidgetItem

from core.editor.models import EditorString


class StringItem(TreeItem[EditorString]):
    """
    Tree item class for strings with a custom sort order.
    """

    @override
    def __lt__(self, other: QTreeWidgetItem) -> bool:
        if not isinstance(other, StringItem):
            return super().__lt__(other)

        if self.item.string.status.value != other.item.string.status.value:
            return self.item.string.status.value > other.item.string.status.value

        return super().__lt__(other)
