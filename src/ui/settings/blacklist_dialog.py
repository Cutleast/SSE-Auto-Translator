"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Optional

from cutleast_core_lib.ui.widgets.search_bar import SearchBar
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class BlacklistDialog(QDialog):
    """
    Dialog for editing author blacklist
    to exclude translations from authors on this list.
    """

    blacklist: list[str]

    def __init__(self, parent: Optional[QWidget], author_blacklist: list[str]):
        super().__init__(parent)

        self.blacklist = author_blacklist

        self.setWindowTitle(self.tr("Blacklist for Translation Authors"))
        self.resize(500, 700)

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        info_label = QLabel(
            self.tr(
                "This is a blacklist to exclude translations from certain authors.\n"
                "All translations from authors on this list below (case-insensitive) "
                "are ignored and do not show up when scanning online.\n"
                "This list only affects translations from Nexus Mods!"
            )
        )
        info_label.setWordWrap(True)
        vlayout.addWidget(info_label)

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        remove_button = QPushButton(self.tr("Remove selected authors from list..."))
        remove_button.setDisabled(True)

        def remove_selected() -> None:
            items = blacklist_widget.selectedItems()
            entries = [item.text() for item in items]

            for entry in entries:
                self.blacklist.remove(entry)

            for item in items:
                blacklist_widget.takeItem(blacklist_widget.indexFromItem(item).row())

        remove_button.clicked.connect(remove_selected)
        hlayout.addWidget(remove_button)

        add_button = QPushButton(self.tr("Add author..."))

        def add_author() -> None:
            dialog = QInputDialog(self)
            dialog.setWindowTitle(self.tr("Add Author..."))
            dialog.setLabelText(self.tr("Enter author name (case-insensitive):"))
            dialog.setInputMode(QInputDialog.InputMode.TextInput)
            dialog.setOkButtonText(self.tr("Ok"))
            dialog.setCancelButtonText(self.tr("Cancel"))
            dialog.setMinimumWidth(800)
            size = dialog.size()
            size.setWidth(800)
            dialog.resize(size)

            if dialog.exec() == dialog.DialogCode.Accepted:
                author_name = dialog.textValue()

                if author_name.lower() not in self.blacklist:
                    self.blacklist.append(author_name.lower())
                    blacklist_widget.addItem(author_name.lower())

        add_button.clicked.connect(add_author)
        hlayout.addWidget(add_button)

        search_bar = SearchBar()

        def search(text_filter: tuple[str, bool]) -> None:
            text: str
            case_sensitive: bool
            text, case_sensitive = text_filter

            for rindex in range(blacklist_widget.count()):
                if case_sensitive:
                    item_visible = text in blacklist_widget.item(rindex).text()
                else:
                    item_visible = (
                        text.lower() in blacklist_widget.item(rindex).text().lower()
                    )

                blacklist_widget.setRowHidden(rindex, not item_visible)

        search_bar.searchChanged.connect(search)
        vlayout.addWidget(search_bar)

        blacklist_widget = QListWidget()
        blacklist_widget.setAlternatingRowColors(True)
        blacklist_widget.setSelectionMode(
            blacklist_widget.SelectionMode.ExtendedSelection
        )

        def on_select() -> None:
            items = blacklist_widget.selectedItems()
            remove_button.setEnabled(bool(items))

        blacklist_widget.itemSelectionChanged.connect(on_select)
        blacklist_widget.addItems(self.blacklist)
        vlayout.addWidget(blacklist_widget)

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        hlayout.addStretch()

        done_button = QPushButton(self.tr("Done"))
        done_button.clicked.connect(self.accept)
        done_button.setDefault(True)
        hlayout.addWidget(done_button)

        cancel_button = QPushButton(self.tr("Cancel"))
        cancel_button.clicked.connect(self.reject)
        hlayout.addWidget(cancel_button)
