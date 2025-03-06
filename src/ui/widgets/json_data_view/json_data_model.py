"""
Copyright (c) Cutleast
"""

from typing import Any, Generic, Optional, TypeAlias, TypeVar, overload, override

from PySide6.QtCore import (
    QAbstractItemModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
)

from .data_item import DataItem
from .dict_item import DictItem
from .list_item import ListItem

T = TypeVar("T")
ModelIndex: TypeAlias = QModelIndex | QPersistentModelIndex


class JsonDataModel(QAbstractItemModel, Generic[T]):
    """
    Model for the JsonDataView widget.
    """

    COLUMN_NAMES: list[str] = ["Key", "Value", "Type"]

    root_item: DataItem

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self.clear()

    @override
    def columnCount(self, parent: Optional[ModelIndex] = None) -> int:
        return len(JsonDataModel.COLUMN_NAMES)

    @override
    def data(self, index: ModelIndex, role: Optional[int] = None) -> Optional[Any]:
        if not index.isValid():
            return None

        item: DataItem = index.internalPointer()

        if role in (Qt.ItemDataRole.UserRole, Qt.ItemDataRole.DisplayRole):
            return item.data(index.column())

        return None

    def clear(self) -> None:
        self.load(None)

    def load(self, obj: Optional[T]) -> None:
        self.beginResetModel()

        self.root_item = JsonDataModel.createItem(name="", value=obj)
        self.root_item.loadChildren()

        self.endResetModel()

    @override
    def setData(self, index: ModelIndex, value: Any, role: Qt.ItemDataRole) -> bool:
        return False

    @override
    def canFetchMore(self, index: ModelIndex) -> bool:
        if not index.isValid():
            return False

        item: DataItem = index.internalPointer()
        return not item.isLoaded

    @override
    def fetchMore(self, index: ModelIndex) -> None:
        self.beginInsertRows(index, index.row(), index.row())

        item: DataItem = index.internalPointer()
        item.loadChildren()

        self.endInsertRows()

    @override
    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole
    ) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if orientation == Qt.Orientation.Horizontal:
            return JsonDataModel.COLUMN_NAMES[section]

    @override
    def rowCount(self, index: ModelIndex) -> int:
        if index.column() > 0:
            return 0

        item: DataItem
        if not index.isValid():
            item = self.root_item
        else:
            item = index.internalPointer()

        return item.childCount()

    @override
    def index(self, row: int, column: int, parent: ModelIndex) -> ModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parent_item: Optional[DataItem]
        if parent.isValid():
            parent_item = parent.internalPointer()
        else:
            parent_item = self.root_item

        child_item: Optional[DataItem] = None
        if parent_item is not None:
            child_item = parent_item.child(row)

        if child_item:
            return self.createIndex(row, column, child_item)

        return QModelIndex()

    @override
    def parent(self, index: ModelIndex) -> ModelIndex:
        if not index.isValid():
            return QModelIndex()

        child_item: DataItem = index.internalPointer()
        parent_item: Optional[DataItem] = child_item.parent()

        if parent_item == self.root_item or parent_item is None:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    @staticmethod
    @overload
    def createItem(name: str, value: list, parent: DataItem) -> ListItem: ...

    @staticmethod
    @overload
    def createItem(name: str, value: dict, parent: DataItem) -> DictItem: ...

    @staticmethod
    @overload
    def createItem(
        name: str, value: T, parent: Optional[DataItem] = None
    ) -> DataItem[T]: ...

    @staticmethod
    def createItem(
        name: str, value: T | list | dict, parent: Optional[DataItem] = None
    ) -> DataItem[T] | ListItem | DictItem:
        match value:
            case list():
                return ListItem(name, value, parent)
            case dict():
                return DictItem(name, value, parent)
            case _:
                return DataItem(name, value, parent)
