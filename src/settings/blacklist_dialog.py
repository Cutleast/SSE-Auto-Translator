"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import utilities as utils
from widgets import SearchBar


class BlacklistDialog(qtw.QDialog):
    """
    Dialog for editing author blacklist
    to exclude translations from authors on this list.
    """

    def __init__(
        self,
        parent: qtw.QWidget,
        author_blacklist: list[str],
        loc: utils.localisation.Localisator,
    ):
        super().__init__(parent)

        self.blacklist = author_blacklist
        self.loc = loc
        self.mloc = loc.blacklist

        self.setWindowTitle(self.mloc.blacklist)
        self.resize(500, 700)

        vlayout = qtw.QVBoxLayout()
        self.setLayout(vlayout)

        info_label = qtw.QLabel(self.mloc.info)
        info_label.setWordWrap(True)
        vlayout.addWidget(info_label)

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        remove_button = qtw.QPushButton(self.loc.main.remove_selected)
        remove_button.setDisabled(True)

        def remove_selected():
            items = blacklist_widget.selectedItems()
            entries = [item.text() for item in items]

            for entry in entries:
                self.blacklist.remove(entry)

            for item in items:
                blacklist_widget.takeItem(blacklist_widget.indexFromItem(item).row())

        remove_button.clicked.connect(remove_selected)
        hlayout.addWidget(remove_button)

        add_button = qtw.QPushButton(self.mloc.add_author)

        def add_author():
            dialog = qtw.QInputDialog(self)
            dialog.setWindowTitle(self.mloc.add_author)
            dialog.setLabelText(self.mloc.enter_author_name)
            dialog.setInputMode(qtw.QInputDialog.InputMode.TextInput)
            dialog.setOkButtonText(self.loc.main.ok)
            dialog.setCancelButtonText(self.loc.main.cancel)
            dialog.setMinimumWidth(800)
            size = dialog.size()
            size.setWidth(800)
            dialog.resize(size)
            utils.apply_dark_title_bar(dialog)

            if dialog.exec() == dialog.DialogCode.Accepted:
                author_name = dialog.textValue()

                if author_name.lower() not in self.blacklist:
                    self.blacklist.append(author_name.lower())
                    blacklist_widget.addItem(author_name.lower())

        add_button.clicked.connect(add_author)
        hlayout.addWidget(add_button)

        search_bar = SearchBar()
        search_bar.setPlaceholderText(self.loc.main.search)
        search_bar.cs_toggle.setToolTip(self.loc.main.case_sensitivity)

        def search(text: str):
            case_sensitive = search_bar.cs_toggle.isChecked()

            for rindex in range(blacklist_widget.count()):
                if case_sensitive:
                    item_visible = text in blacklist_widget.item(rindex).text()
                else:
                    item_visible = (
                        text.lower() in blacklist_widget.item(rindex).text().lower()
                    )

                blacklist_widget.setRowHidden(rindex, not item_visible)

        search_bar.textChanged.connect(search)
        vlayout.addWidget(search_bar)

        blacklist_widget = qtw.QListWidget()
        blacklist_widget.setAlternatingRowColors(True)
        blacklist_widget.setSelectionMode(
            blacklist_widget.SelectionMode.ExtendedSelection
        )

        def on_select():
            items = blacklist_widget.selectedItems()
            remove_button.setEnabled(bool(items))

        blacklist_widget.itemSelectionChanged.connect(on_select)
        blacklist_widget.addItems(self.blacklist)
        vlayout.addWidget(blacklist_widget)

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        hlayout.addStretch()

        done_button = qtw.QPushButton(self.loc.main.done)
        done_button.clicked.connect(self.accept)
        hlayout.addWidget(done_button)

        cancel_button = qtw.QPushButton(self.loc.main.cancel)
        cancel_button.clicked.connect(self.reject)
        hlayout.addWidget(cancel_button)
