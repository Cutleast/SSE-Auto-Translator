"""
Copyright (c) Cutleast
"""

import os
import re
from pathlib import Path
from typing import Optional

import pyperclip
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app_context import AppContext
from core.database.string import String
from core.database.translation import Translation
from core.editor.editor import Editor
from ui.translation_editor.editor.help_dialog import EditorHelpDialog
from ui.widgets.lcd_number import LCDNumber
from ui.widgets.loading_dialog import LoadingDialog
from ui.widgets.search_bar import SearchBar
from ui.widgets.stacked_bar import StackedBar

from .editor_menu import EditorMenu
from .editor_toolbar import EditorToolbar
from .strings_widget import StringsWidget
from .translator_dialog import TranslatorDialog


class EditorTab(QWidget):
    """
    Class for editor tabs.
    """

    __editor: Editor

    translation: Translation
    plugin_name: Optional[str]

    changes_pending: bool = False
    changes_pending_signal = Signal(bool)
    """
    This signal gets emitted when the changes pending state changes.
    """

    __vlayout: QVBoxLayout
    __title_label: QLabel
    __tool_bar: EditorToolbar
    __menu: EditorMenu

    def __init__(self, translation: Translation, plugin_name: Optional[str] = None):
        super().__init__()

        self.translation = translation
        self.plugin_name = plugin_name

        self.changes_pending_signal.connect(self.__on_change)

        self.__editor = Editor(translation, plugin_name)
        self.__editor.update_signal.connect(self.update)
        self.__editor.update_signal.connect(
            lambda: self.changes_pending_signal.emit(True)
        )

        self.__init_ui()
        self.__init_shortcuts()

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_strings_widget()
        self.__init_context_menu()
        self.update()

    def __init_header(self) -> None:
        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        self.__title_label = QLabel(
            f"{self.translation.name} > {self.plugin_name}"
            if self.plugin_name
            else self.translation.name
        )
        self.__title_label.setObjectName("relevant_label")
        hlayout.addWidget(self.__title_label)

        hlayout.addStretch()

        num_label = QLabel(self.tr("Strings") + ":")
        num_label.setObjectName("relevant_label")
        hlayout.addWidget(num_label)

        self.__strings_num_label = LCDNumber()
        self.__strings_num_label.setDigitCount(6)
        hlayout.addWidget(self.__strings_num_label)

        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        self.__tool_bar = EditorToolbar(self)
        hlayout.addWidget(self.__tool_bar)

        self.__search_bar = SearchBar()
        self.__search_bar.searchChanged.connect(self.set_name_filter)
        hlayout.addWidget(self.__search_bar)

        self.__bar_chart = StackedBar(
            [0 for s in String.Status],
            colors=[
                String.Status.get_color(s) or Qt.GlobalColor.white
                for s in String.Status
            ],
        )
        self.__bar_chart.setFixedHeight(3)
        self.__vlayout.addWidget(self.__bar_chart)

    def __init_strings_widget(self) -> None:
        self.__strings_widget = StringsWidget(self, self.__editor.strings)
        self.__strings_widget.itemSelectionChanged.connect(
            lambda: (
                self.__tool_bar.search_and_replace_action.setEnabled(
                    bool(self.__strings_widget.selectedItems())
                ),
                self.__tool_bar.api_translation_action.setEnabled(
                    bool(self.__strings_widget.selectedItems())
                ),
            ),
        )
        self.__vlayout.addWidget(self.__strings_widget)
        self.__strings_widget.itemActivated.connect(
            lambda item, col: self.open_translator_dialog()
        )

    def __init_shortcuts(self) -> None:
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save)

        # TODO: Reimplement this
        # close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        # close_shortcut.activated.connect(
        #     lambda: app.translation_editor.close_translation(translation)
        # )

        complete_shortcut = QShortcut(QKeySequence("F1"), self)
        incomplete_shortcut = QShortcut(QKeySequence("F2"), self)
        no_required_shortcut = QShortcut(QKeySequence("F3"), self)
        reset_shortcut = QShortcut(QKeySequence("F4"), self)

        complete_shortcut.activated.connect(
            lambda: self.set_status(String.Status.TranslationComplete)
        )

        incomplete_shortcut.activated.connect(
            lambda: self.set_status(String.Status.TranslationIncomplete)
        )

        no_required_shortcut.activated.connect(
            lambda: self.set_status(String.Status.NoTranslationRequired)
        )

        reset_shortcut.activated.connect(self.reset_translation)

    def __init_context_menu(self) -> None:
        self.__menu = EditorMenu(self)

        self.__strings_widget.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.__strings_widget.customContextMenuRequested.connect(self.__menu.open)

    def __on_change(self, changes_pending: bool = True) -> None:
        self.changes_pending = changes_pending

    def import_legacy(self) -> None:
        """
        Opens file dialog to choose a DSD JSON of pre-v1.1 format.
        """

        fdialog = QFileDialog()
        fdialog.setFileMode(fdialog.FileMode.ExistingFile)
        fdialog.setNameFilters([self.tr("DSD File (*.json)")])
        fdialog.setWindowTitle(self.tr("Import pre-v1.1 Translation..."))

        if fdialog.exec() == fdialog.DialogCode.Rejected:
            return

        selected_files = fdialog.selectedFiles()

        if len(selected_files):
            filepath = Path(selected_files.pop(0))
            if not filepath.is_file():
                return

            self.__editor.import_legacy_dsd_translation(filepath)

    def open_translator_dialog(self, string: Optional[String] = None) -> None:
        """
        Opens a string in a translator dialog.

        Args:
            string (Optional[String]): String to open. Defaults to the current string.
        """

        if string is None:
            string = self.__strings_widget.get_current_string()

        if string is not None:
            assert string in self.__editor.strings

            dialog = TranslatorDialog(self, string)
            dialog.update_signal.connect(self.update)
            dialog.show()

    def update_matching_strings(self, original: str, translation: str) -> None:
        """
        Update strings that are matching
        """

        self.__editor.apply_to_matching_strings(original, translation)

    def get_string_states_summary(self) -> dict[String.Status, int]:
        """
        Get a summary of string states.

        Returns:
            dict[String.Status, int]:
                Dictionary of string states and number of strings in each state
        """

        return {
            state: len(
                [string for string in self.__editor.strings if string.status == state]
            )
            for state in String.Status
        }

    def get_visible_strings(self) -> list[String]:
        """
        Get a list of all strings that are visible with the current filter.

        Returns:
            list[String]: The visible strings
        """

        strings: list[String] = self.__strings_widget.get_visible_strings()
        return strings

    def get_index(self, string: String) -> int:
        """
        Gets the index of a string in the list.

        Args:
            string (String): The string to get the index of.

        Returns:
            int: The index
        """

        index: int = self.__strings_widget.get_index_of_string(string)
        return index

    def update(self) -> None:
        """
        Updates visible string list.
        """

        self.__strings_widget.update()

        if self.changes_pending:
            self.__title_label.setText(
                f"{self.translation.name} > {self.plugin_name}*"
                if self.plugin_name
                else self.translation.name
            )
        else:
            self.__title_label.setText(
                f"{self.translation.name} > {self.plugin_name}"
                if self.plugin_name
                else self.translation.name
            )

        summary: dict[String.Status, int] = self.get_string_states_summary()

        self.__strings_num_label.display(len(self.__editor.strings))
        self.__bar_chart.setValues(list(summary.values()))

        num_tooltip = ""

        for status, count in summary.items():
            color: Optional[QColor] = String.Status.get_color(status)

            if color is None:
                num_tooltip += f"<tr><td>{status.get_localized_name()}:\
                    </td><td align=right>{count}</td></tr>"
            else:
                num_tooltip += f"<tr><td><font color='{color.name()}'>{status.get_localized_name()}:\
                    </font></td><td align=right><font color='{color.name()}'>{count}</font></td></tr>"

        self.__strings_num_label.setToolTip(num_tooltip)
        self.__bar_chart.setToolTip(num_tooltip)

    def save(self) -> None:
        """
        Saves translation.
        """

        self.__editor.save()
        self.changes_pending_signal.emit(False)

    @property
    def __selected_string_ids(self) -> list[str]:
        return [string.id for string in self.__strings_widget.get_selected_strings()]

    def apply_database(self) -> None:
        """
        Applies database to untranslated strings.
        """

        modified_strings: int = self.__editor.apply_database(self.__selected_string_ids)

        messagebox = QMessageBox(QApplication.activeModalWidget())
        messagebox.setWindowTitle(self.tr("Success!"))
        messagebox.setText(
            self.tr(
                "Translated %n String with database.",
                "Translated %n Strings with database.",
                modified_strings,
            )
        )
        messagebox.exec()

    def search_and_replace(self) -> None:
        """
        Opens dialog for advanced search and replace operations.
        """

        dialog = QDialog(QApplication.activeModalWidget())
        dialog.setMinimumWidth(700)
        dialog.setWindowTitle(self.tr("Search and Replace"))

        vlayout = QVBoxLayout()
        dialog.setLayout(vlayout)

        flayout = QFormLayout()
        vlayout.addLayout(flayout)

        search_entry = QLineEdit()
        flayout.addRow(self.tr("Search"), search_entry)

        replace_entry = QLineEdit()
        flayout.addRow(self.tr("Replace"), replace_entry)

        case_sensitivity_checkbox = QCheckBox(self.tr("Case Sensitive"))
        flayout.addRow(case_sensitivity_checkbox)

        vlayout.addStretch()

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        hlayout.addStretch()

        apply_button = QPushButton(self.tr("Apply"))
        apply_button.setObjectName("accent_button")
        apply_button.setDefault(True)
        apply_button.clicked.connect(dialog.accept)
        hlayout.addWidget(apply_button)

        cancel_button = QPushButton(self.tr("Cancel"))
        cancel_button.clicked.connect(dialog.reject)
        hlayout.addWidget(cancel_button)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            pattern: re.Pattern
            if case_sensitivity_checkbox.isChecked():
                pattern = re.compile(re.escape(search_entry.text()))
            else:
                pattern = re.compile(re.escape(search_entry.text()), re.IGNORECASE)

            self.__editor.apply_regex(
                self.__selected_string_ids, replace_entry.text(), pattern
            )

    def translate_with_api(self) -> None:
        """
        Opens dialog to configure batch translation via user configured API.
        """

        if AppContext.get_app().translator_config.show_confirmation_dialogs:
            dialog = QDialog(QApplication.activeModalWidget())
            dialog.setWindowTitle(self.tr("Translate with API"))

            vlayout = QVBoxLayout()
            dialog.setLayout(vlayout)

            label = QLabel(
                self.tr(
                    "Are you sure you want to translate %n String via Translator API?\n"
                    "Depending on the Translator API this can raise unexpected costs.",
                    "Are you sure you want to translate %n Strings via Translator API?\n"
                    "Depending on the Translator API this can raise unexpected costs.",
                    len(self.__selected_string_ids),
                )
            )
            vlayout.addWidget(label)

            vlayout.addStretch()

            hlayout = QHBoxLayout()
            vlayout.addLayout(hlayout)

            hlayout.addStretch()

            apply_button = QPushButton(self.tr("Apply"))
            apply_button.clicked.connect(dialog.accept)
            hlayout.addWidget(apply_button)

            cancel_button = QPushButton(self.tr("Cancel"))
            cancel_button.clicked.connect(dialog.reject)
            hlayout.addWidget(cancel_button)

            do_not_show_again_checkbox = QCheckBox(self.tr("Don't show again"))
            hlayout.addWidget(do_not_show_again_checkbox)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                if do_not_show_again_checkbox.isChecked():
                    AppContext.get_app().translator_config.show_confirmation_dialogs = (
                        False
                    )
                    AppContext.get_app().translator_config.save()
            else:
                return

        LoadingDialog.run_callable(
            QApplication.activeModalWidget(),
            lambda ldialog: self.__editor.translate_with_api(
                self.__selected_string_ids, ldialog
            ),
        )

    def export(self) -> None:
        """
        Exports translation in DSD format to a user selected path.
        """

        file_dialog = QFileDialog(QApplication.activeModalWidget())
        file_dialog.setWindowTitle(self.tr("Export Translation (DSD Format only)"))
        file_dialog.setFileMode(QFileDialog.FileMode.Directory)

        if file_dialog.exec():
            folder = file_dialog.selectedFiles()[0]
            folder = os.path.normpath(folder)
            folder_path = Path(folder)

            self.translation.export(folder_path)

            messagebox = QMessageBox(QApplication.activeModalWidget())
            messagebox.setWindowTitle(self.tr("Success!"))
            messagebox.setText(self.tr("Translation successfully exported."))
            messagebox.exec()

    def show_help(self) -> None:
        """
        Displays help popup.
        """

        EditorHelpDialog(QApplication.activeModalWidget()).exec()

    def set_status(self, status: String.Status) -> None:
        selected_items: list[String] = self.__strings_widget.get_selected_strings()
        self.__editor.set_status([string.id for string in selected_items], status)

    def reset_translation(self) -> None:
        selected_items: list[String] = self.__strings_widget.get_selected_strings()

        if not selected_items:
            return

        message_box = QMessageBox(QApplication.activeModalWidget())
        message_box.setWindowTitle(self.tr("Reset selected String(s)"))
        message_box.setText(self.tr("Reset selected String(s)"))
        message_box.setStandardButtons(
            QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes
        )
        message_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        message_box.button(QMessageBox.StandardButton.No).setText(self.tr("No"))
        message_box.button(QMessageBox.StandardButton.Yes).setText(self.tr("Yes"))
        choice = message_box.exec()

        if choice == QMessageBox.StandardButton.Yes:
            self.__editor.reset_strings([string.id for string in selected_items])

    def copy_selected(self) -> None:
        """
        Copies current selected strings to clipboard.
        """

        selected_items = self.__strings_widget.selectedItems()

        clipboard_text = ""
        for item in selected_items:
            for c in range(self.__strings_widget.columnCount()):
                clipboard_text += f"{item.toolTip(c)!r}"[1:-1] + "\t"

            clipboard_text = clipboard_text.removesuffix("\t")
            clipboard_text += "\n"

        pyperclip.copy(clipboard_text.strip())

    def set_name_filter(self, name_filter: tuple[str, bool]) -> None:
        """
        Sets the name filter.

        Args:
            name_filter (tuple[str, bool]): The name to filter by and case-sensitivity.
        """

        self.__strings_widget.set_name_filter(name_filter)
        self.update()

    def set_state_filter(self, state_filter: list[String.Status]) -> None:
        """
        Sets the state filter.

        Args:
            state_filter (list[String.Status]): The states to filter by.
        """

        self.__strings_widget.set_state_filter(state_filter)
        self.update()