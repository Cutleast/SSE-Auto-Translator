"""
Copyright (c) Cutleast
"""

from dataclasses import dataclass
from typing import Any, override

from .data_item import DataItem


@dataclass
class DictItem(DataItem[dict[str, Any]]):
    """
    Class for dictionary nodes in the JsonDataView widget.
    """

    @override
    def loadChildren(self) -> None:
        from .json_data_model import JsonDataModel

        self.children = []
        for key, value in self.value.items():
            self.children.append(
                JsonDataModel.createItem(name=key[:100], value=value, parent=self)
            )

    @override
    def childCount(self) -> int:
        return len(self.value)

    @property
    @override
    def display_value(self) -> str:
        return f"[{len(self.value)}]"
