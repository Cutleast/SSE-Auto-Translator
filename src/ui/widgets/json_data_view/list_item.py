"""
Copyright (c) Cutleast
"""

from dataclasses import dataclass
from typing import override

from .data_item import DataItem


@dataclass
class ListItem(DataItem[list]):
    """
    Class for list nodes in the JsonDataView widget.
    """

    @override
    def loadChildren(self) -> None:
        from .json_data_model import JsonDataModel

        self.children = []
        for i, item in enumerate(self.value):
            self.children.append(
                JsonDataModel.createItem(name=str(i), value=item, parent=self)
            )

    @override
    def childCount(self) -> int:
        return len(self.value)

    @property
    @override
    def display_value(self) -> str:
        return f"[{len(self.value)}]"
