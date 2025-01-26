"""
Copyright (c) Cutleast
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class DataItem(Generic[T]):
    """
    Abstract base class for item nodes in the JsonDataView widget.
    """

    display_name: str
    """
    The node's display name.
    """

    value: T
    """
    The node's value.
    """

    parentItem: Optional[DataItem] = None
    """
    The node's parent.
    """

    children: Optional[list[DataItem]] = None
    """
    The node's children.
    """

    def loadChildren(self) -> None:
        """
        Loads the node's children.
        """

        self.children = []

    @property
    def isLoaded(self) -> bool:
        """
        Whether the node's children have been loaded.
        """

        return self.children is not None

    @property
    def display_value(self) -> str:
        """
        The node's value as a string.
        """

        return str(self.value)

    def child(self, row: int) -> DataItem:
        if self.children is None:
            raise ValueError("Children have not been loaded yet.")

        return self.children[row]

    def childCount(self) -> int:
        if self.children is None:
            # raise ValueError("Children have not been loaded yet.")
            return 0

        return len(self.children)

    def columnCount(self) -> int:
        from .json_data_model import JsonDataModel

        return len(JsonDataModel.COLUMN_NAMES)

    def data(self, column: int) -> Any:
        if column == 0:
            return self.display_name
        elif column == 1:
            return self.display_value
        elif column == 2:
            return str(type(self.value))

        return None

    def parent(self) -> Optional[DataItem]:
        return self.parentItem

    def row(self) -> int:
        if self.parentItem is not None and self.parentItem.children is not None:
            return self.parentItem.children.index(self)

        return 0
