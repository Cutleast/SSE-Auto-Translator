"""
Copyright (c) Cutleast
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QRadioButton,
    QWidget,
)

from core.string.search_filter import SearchFilter
from ui.utilities.theme_manager import ThemeManager

from .shortcut_button import ShortcutButton


class StringSearchDialog(QDialog):
    """
    Dialog for the user to create a search filter for strings in the modlist or database.
    """

    __translations: bool

    __id_box: QCheckBox
    __id_entry: QLineEdit
    __original_box: QRadioButton
    __original_entry: QLineEdit
    __string_box: QRadioButton | QCheckBox
    __string_entry: QLineEdit

    def __init__(self, parent: Optional[QWidget], translations: bool = True):
        super().__init__(parent)

        self.setWindowTitle(self.tr("Search for a string..."))
        self.setModal(True)
        self.setMinimumWidth(700)

        self.__translations = translations

        self.__init_ui()

        self.__original_box.setVisible(self.__translations)
        self.__original_entry.setVisible(self.__translations)

    def __init_ui(self) -> None:
        flayout = QFormLayout()
        self.setLayout(flayout)

        self.__id_box = QCheckBox(self.tr("ID"))
        self.__id_entry = QLineEdit()
        self.__id_entry.setDisabled(True)
        self.__id_box.stateChanged.connect(
            lambda state: self.__id_entry.setEnabled(
                state == Qt.CheckState.Checked.value
            )
        )
        self.__id_box.clicked.connect(self.__id_entry.setFocus)
        flayout.addRow(self.__id_box, self.__id_entry)

        self.__original_box = QRadioButton(self.tr("Original"))
        self.__original_entry = QLineEdit()
        self.__original_entry.setDisabled(True)
        self.__original_box.toggled.connect(
            lambda: self.__original_entry.setEnabled(self.__original_box.isChecked())
        )
        self.__original_box.clicked.connect(self.__original_entry.setFocus)
        flayout.addRow(self.__original_box, self.__original_entry)

        if self.__translations:
            self.__string_box = QRadioButton(self.tr("String"))
        else:
            self.__string_box = QCheckBox(self.tr("String"))
        self.__string_entry = QLineEdit()
        self.__string_entry.setDisabled(True)
        self.__string_box.toggled.connect(
            lambda: self.__string_entry.setEnabled(self.__string_box.isChecked())
        )
        self.__string_box.clicked.connect(self.__string_entry.setFocus)
        flayout.addRow(self.__string_box, self.__string_entry)

        hlayout = QHBoxLayout()
        flayout.addRow(hlayout)

        cancel_button = ShortcutButton(self.tr("Cancel"))
        cancel_button.setShortcut(QKeySequence("Esc"))
        cancel_button.clicked.connect(self.reject)
        hlayout.addWidget(cancel_button)

        hlayout.addStretch()

        search_button = ShortcutButton(self.tr("Search"))
        search_button.setDefault(True)
        search_button.setShortcut(QKeySequence("Return"))
        search_button.clicked.connect(self.accept)
        hlayout.addWidget(search_button)

        # Reapply stylesheet as setDefaultButton() doesn't update the style by itself
        self.setStyleSheet(ThemeManager.get_stylesheet() or "")

    def get_filter(self) -> SearchFilter:
        """
        Get the search filter as a dictionary.

        Returns:
            SearchFilter: The search filter.
        """

        filter: SearchFilter = {}

        if self.__id_box.isChecked():
            filter["id"] = self.__id_entry.text()

        if (
            self.__original_box.isChecked()
            and self.__original_entry.text()
            and self.__translations
        ):
            filter["original"] = self.__original_entry.text()
        elif (
            self.__string_box.isChecked()
            and self.__string_entry.text()
            and self.__translations
        ):
            filter["string"] = self.__string_entry.text()
        elif self.__string_box.isChecked() and self.__string_entry.text():
            filter["original"] = self.__string_entry.text()

        return filter
