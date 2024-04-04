import sys
from pathlib import Path

import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import utilities as utils
from plugin_parser import PluginParser


class AttributeModel(qtg.QStandardItemModel):
    def __init__(self, data, parent=None):
        super().__init__(0, 2, parent)
        self.setHorizontalHeaderLabels(["Attribute", "Value"])
        self.setup_data(data)

    def setup_data(self, data):
        self.removeRows(0, self.rowCount())
        for key, value in data.items():
            parent_item = qtg.QStandardItem(str(key))
            if isinstance(value, dict):
                self.appendRow([parent_item, qtg.QStandardItem()])
                nested_model = AttributeModel(value)
                self.setItem(self.rowCount() - 1, 1, nested_model.invisibleRootItem())
            else:
                self.appendRow([parent_item, qtg.QStandardItem(str(value))])


def get_attributes(cls):
    attributes = {}
    for attribute_name, attribute_type in cls.__annotations__.items():
        if isinstance(attribute_type, str):
            attributes[attribute_name] = attribute_type
        elif hasattr(attribute_type, "__annotations__"):
            attributes[attribute_name] = get_attributes(attribute_type)
    return attributes


class MainWindow(qtw.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Attribute Viewer")
        self.setGeometry(100, 100, 600, 400)

        self.tree_view = qtw.QTreeView(self)
        self.setCentralWidget(self.tree_view)

        parser = PluginParser(Path("..\\tests\\Obsidian Weathers.esp"))
        plugin = parser.parse_plugin()
        print(plugin)

        plugin_attributes = get_attributes(plugin)
        model = AttributeModel(plugin_attributes)
        self.tree_view.setModel(model)


if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
