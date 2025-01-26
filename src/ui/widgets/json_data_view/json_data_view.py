"""
Copyright (c) Cutleast
"""

from typing import Any, Optional

import qtawesome as qta
from PySide6.QtCore import QModelIndex, QPoint, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QMenu, QTreeView, QWidget

from core.utilities.container_utils import unique

from .data_item import DataItem
from .json_data_model import JsonDataModel


class JsonDataView(QTreeView):
    """
    A QTreeView specialized for displaying complex json data structures.
    """

    __model: JsonDataModel

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.__model = JsonDataModel(self)
        self.setModel(self.__model)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        self.setUniformRowHeights(True)

        copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, self)
        copy_shortcut.activated.connect(self.copy_selected_items)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__on_context_menu)

    def __on_context_menu(self, point: QPoint) -> None:
        menu = QMenu()

        expand_all_action = menu.addAction(
            qta.icon("mdi6.arrow-expand-vertical", color="#ffffff"),
            self.tr("Expand all"),
        )
        expand_all_action.triggered.connect(self.expandAll)

        collapse_all_action = menu.addAction(
            qta.icon("mdi6.arrow-collapse-vertical", color="#ffffff"),
            self.tr("Collapse all"),
        )
        collapse_all_action.triggered.connect(self.collapseAll)

        menu.addSeparator()

        copy_action = menu.addAction(
            qta.icon("mdi6.content-copy", color="#ffffff"), self.tr("Copy")
        )
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self.copy_selected_items)

        menu.exec(self.mapToGlobal(point))

    def copy_selected_items(self) -> None:
        """
        Copies the selected items to the clipboard.
        """

        indexes: list[QModelIndex] = self.selectedIndexes()
        selected_items: list[DataItem] = [
            index.internalPointer() for index in sorted(indexes, key=lambda i: i.row())
        ]

        text: str = "\n".join(unique(self.__copy_item(item) for item in selected_items))

        QApplication.clipboard().setText(text)

    def __copy_item(self, item: DataItem) -> str:
        return f"{item.display_name}\t{item.display_value}\t{type(item.value)}"

    def set_data(self, data: Any) -> None:
        """
        Sets the data to be displayed.

        Args:
            data (Any): The data to be displayed.
        """

        self.__model.load(data)

        for c in range(3):
            self.resizeColumnToContents(c)


def test() -> None:
    app = QApplication()

    widget = JsonDataView()
    widget.show()
    widget.resize(800, 600)

    TEST_DATA = {
        "name": "John Doe",
        "age": 30,
        "children": [
            {
                "name": "Alice",
                "age": 5,
            }
        ],
    }
    widget.set_data(TEST_DATA)

    app.exec()


if __name__ == "__main__":
    test()
