"""
Copyright (c) Cutleast
"""

from typing import Any, Optional

import qtawesome as qta
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem, QWidget
from PySide6.QtWidgets import QMenu as Menu

# from .menu import Menu


class JsonDataView(QTreeWidget):
    """
    A QTreeWidget specialized for displaying complex json data structures.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.setHeaderLabels([self.tr("Key"), self.tr("Value/Size"), self.tr("Type")])
        self.setColumnCount(3)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)

        copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, self)
        copy_shortcut.activated.connect(self.copy_selected_items)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__on_context_menu)

    def __on_context_menu(self, point: QPoint) -> None:
        menu = Menu()

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

        selected_items = self.selectedItems()
        text: str = "\n".join(self.__copy_item(item) for item in selected_items)

        QApplication.clipboard().setText(text)

    def __copy_item(self, item: QTreeWidgetItem) -> str:
        return "\t".join(item.text(c) for c in range(self.columnCount()))

    def set_data(self, data: Any) -> None:
        """
        Sets the data to be displayed.

        Args:
            data (Any): The data to be displayed.
        """

        self.clear()

        self.addTopLevelItems(self.__process_item(data).takeChildren())

        self.expandAll()
        for c in range(3):
            self.resizeColumnToContents(c)

    def __process_item(self, data: Any, name: Optional[str] = None) -> QTreeWidgetItem:
        item = QTreeWidgetItem(["", "", ""])
        items: list[QTreeWidgetItem]
        match data:
            case list():
                items = self.__process_list(data)
                item.addChildren(items)
                item.setText(1, str(len(items)))
            case dict():
                items = self.__process_dict(data)
                item.addChildren(items)
            case _:
                item.setText(1, str(data))

        if name is not None:
            item.setText(0, name)

        item.setText(2, type(data).__name__)

        return item

    def __process_list(self, data: list) -> list[QTreeWidgetItem]:
        items: list[QTreeWidgetItem] = []
        for index, value in enumerate(data):
            items.append(self.__process_item(value, name=str(index)))

        return items

    def __process_dict(self, data: dict[str, Any]) -> list[QTreeWidgetItem]:
        items: list[QTreeWidgetItem] = []
        for key, value in data.items():
            items.append(self.__process_item(value, name=key))

        return items


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
