"""
Copyright (c) Cutleast
"""

from typing import Optional, TypeAlias

from cutleast_core_lib.core.utilities.exceptions import format_exception
from cutleast_core_lib.core.utilities.filter import matches_filter
from cutleast_core_lib.ui.utilities.tree_widget import (
    get_visible_top_level_item_count,
    iter_toplevel_items,
)
from cutleast_core_lib.ui.widgets.line_number_text_edit import LineNumberTextEdit
from cutleast_core_lib.ui.widgets.search_bar import SearchBar
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

Report: TypeAlias = dict[str, Exception]
"""Type alias for a dict mapping an item display name and an exception."""


class ReportDialog(QDialog):
    """
    Dialog for displaying details about failed items after a batch process.
    """

    __report: Report

    __vlayout: QVBoxLayout

    __search_bar: SearchBar
    __item_num_label: QLabel

    __splitter: QSplitter
    __item_list: QTreeWidget
    __details_box: QPlainTextEdit

    def __init__(self, report: Report, parent: Optional[QWidget] = None) -> None:
        """
        Args:
            report (Report): A dict mapping an item display name and an exception.
            parent (Optional[QWidget], optional):
                Optional parent widget. Defaults to None.
        """

        super().__init__(parent)

        self.__report = report

        self.__init_ui()
        self.__init_items()

        self.__search_bar.searchChanged.connect(self.__on_search_changed)
        self.__item_list.currentItemChanged.connect(self.__on_item_activated)

        self.resize(800, 600)

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_splitter()
        self.__init_footer()

    def __init_header(self) -> None:
        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        self.__search_bar = SearchBar()
        hlayout.addWidget(self.__search_bar)

        num_label = QLabel(self.tr("Failed items:"))
        num_label.setProperty("subtitle", True)
        hlayout.addWidget(num_label)

        self.__item_num_label = QLabel()
        self.__item_num_label.setProperty("subtitle", True)
        hlayout.addWidget(self.__item_num_label)

    def __init_splitter(self) -> None:
        self.__splitter = QSplitter()
        self.__splitter.setOrientation(Qt.Orientation.Horizontal)
        self.__vlayout.addWidget(self.__splitter, stretch=1)

        self.__item_list = QTreeWidget()
        self.__item_list.setIndentation(0)  # no indentation necessary
        self.__item_list.setHeaderHidden(True)
        self.__item_list.setProperty("no_header", True)
        self.__item_list.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.__splitter.addWidget(self.__item_list)

        self.__details_box = LineNumberTextEdit()
        self.__details_box.setProperty("monospace", True)
        self.__splitter.addWidget(self.__details_box)

    def __init_footer(self) -> None:
        ok_button = QPushButton(self.tr("Ok"))
        ok_button.setDefault(True)
        ok_button.clicked.connect(self.accept)
        self.__vlayout.addWidget(ok_button)

    def __init_items(self) -> None:
        for item_name in self.__report:
            item = QTreeWidgetItem([item_name])
            self.__item_list.addTopLevelItem(item)

        self.__item_num_label.setText(str(len(self.__report)))

    def __on_item_activated(self, item: QTreeWidgetItem, prev: QTreeWidgetItem) -> None:
        self.__details_box.setPlainText(format_exception(self.__report[item.text(0)]))

    def __on_search_changed(self, text: str, case_sensitive: bool) -> None:
        for item in iter_toplevel_items(self.__item_list):
            item.setHidden(
                not matches_filter(item.text(0), text, case_sensitive or False)
            )

        self.__item_num_label.setText(
            str(get_visible_top_level_item_count(self.__item_list))
        )
