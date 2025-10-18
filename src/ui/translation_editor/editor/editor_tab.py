"""
Copyright (c) Cutleast
"""

import os
import re
from pathlib import Path
from typing import Optional, override

from cutleast_core_lib.ui.widgets.lcd_number import LCDNumber
from cutleast_core_lib.ui.widgets.loading_dialog import LoadingDialog
from cutleast_core_lib.ui.widgets.search_bar import SearchBar
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

from core.config.app_config import AppConfig
from core.database.exporter import Exporter
from core.database.translation import Translation
from core.editor.editor import Editor
from core.string import String, StringList
from core.string.plugin_string import PluginString
from core.string.string_status import StringStatus
from core.translator_api.translator import Translator
from core.user_data.user_data import UserData
from ui.translation_editor.editor.help_dialog import EditorHelpDialog
from ui.utilities.theme_manager import ThemeManager
from ui.widgets.stacked_bar import StackedBar

from .editor_menu import EditorMenu
from .editor_toolbar import EditorToolbar
from .strings_widget import StringsWidget
from .translator_dialog import TranslatorDialog


class EditorTab(QWidget):
    """
    Class for editor tabs.
    """

    close_signal = Signal(Translation)
    """
    This signal gets emitted when tab is to be closed.
    """

    __editor: Editor

    translation: Translation
    app_config: AppConfig
    user_data: UserData
    translator: Translator

    __vlayout: QVBoxLayout
    __title_label: QLabel
    __tool_bar: EditorToolbar
    __menu: EditorMenu
    __strings_widget: StringsWidget

    def __init__(
        self,
        translation: Translation,
        app_config: AppConfig,
        user_data: UserData,
        translator: Translator,
    ) -> None:
        super().__init__()

        self.translation = translation
        self.app_config = app_config
        self.user_data = user_data
        self.translator = translator

        self.__editor = Editor(
            translation, user_data.user_config.language, user_data.database, translator
        )
        self.__editor.update_signal.connect(self.update)

        self.__init_ui()
        self.__init_shortcuts()

        self.__tool_bar.filter_changed.connect(self.set_state_filter)
        self.__tool_bar.help_requested.connect(self.__show_help)
        self.__tool_bar.legacy_import_requested.connect(self.__import_legacy)
        self.__tool_bar.apply_database_requested.connect(self.__apply_database)
        self.__tool_bar.search_and_replace_requested.connect(self.__search_and_replace)
        self.__tool_bar.api_translation_requested.connect(self.__translate_with_api)
        self.__tool_bar.save_requested.connect(self.__save)
        self.__tool_bar.export_requested.connect(self.__export)

        self.__menu.expand_all_clicked.connect(self.expandAll)
        self.__menu.collapse_all_clicked.connect(self.collapseAll)
        self.__menu.edit_string_requested.connect(self.__edit_string)
        self.__menu.copy_string_requested.connect(self.__copy_selected)
        self.__menu.reset_translation_requested.connect(self.__reset_selected)
        self.__menu.mark_as_requested.connect(self.__set_status)

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

        self.__title_label = QLabel(self.translation.name)
        self.__title_label.setObjectName("h3")
        hlayout.addWidget(self.__title_label)

        hlayout.addStretch()

        num_label = QLabel(self.tr("Strings") + ":")
        num_label.setObjectName("h3")
        hlayout.addWidget(num_label)

        self.__strings_num_label = LCDNumber()
        self.__strings_num_label.setDigitCount(6)
        hlayout.addWidget(self.__strings_num_label)

        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        self.__tool_bar = EditorToolbar()
        hlayout.addWidget(self.__tool_bar)

        self.__search_bar = SearchBar()
        self.__search_bar.searchChanged.connect(self.set_name_filter)
        hlayout.addWidget(self.__search_bar)

        self.__bar_chart = StackedBar(
            [0 for _ in StringStatus],
            colors=[
                StringStatus.get_color(s) or Qt.GlobalColor.white for s in StringStatus
            ],
        )
        self.__bar_chart.setFixedHeight(3)
        self.__vlayout.addWidget(self.__bar_chart)

    def __init_strings_widget(self) -> None:
        self.__strings_widget = StringsWidget(self.__editor.strings)
        self.__strings_widget.itemSelectionChanged.connect(
            lambda: self.__tool_bar.set_edit_actions_enabled(
                len(self.__strings_widget.get_selected_strings()) > 0
            ),
        )
        self.__vlayout.addWidget(self.__strings_widget)
        self.__strings_widget.itemActivated.connect(
            lambda item, col: self.__edit_string()
        )
        self.__strings_num_label.setDigitCount(
            max((len(str(self.__strings_widget.get_visible_string_count())), 4))
        )

    def __init_shortcuts(self) -> None:
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.__save)

        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(
            lambda: self.close_signal.emit(self.translation)
        )

        complete_shortcut = QShortcut(QKeySequence("F1"), self)
        incomplete_shortcut = QShortcut(QKeySequence("F2"), self)
        no_required_shortcut = QShortcut(QKeySequence("F3"), self)
        reset_shortcut = QShortcut(QKeySequence("F4"), self)

        complete_shortcut.activated.connect(
            lambda: self.__set_status(StringStatus.TranslationComplete)
        )

        incomplete_shortcut.activated.connect(
            lambda: self.__set_status(StringStatus.TranslationIncomplete)
        )

        no_required_shortcut.activated.connect(
            lambda: self.__set_status(StringStatus.NoTranslationRequired)
        )

        reset_shortcut.activated.connect(self.__reset_selected)

    def __init_context_menu(self) -> None:
        self.__menu = EditorMenu()

        self.__strings_widget.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.__strings_widget.customContextMenuRequested.connect(self.__menu.open)

    @property
    def changes_pending(self) -> bool:
        """
        Whether there are unsaved changes.
        """

        return self.__editor.changes_pending

    def __import_legacy(self) -> None:
        """
        Opens file dialog to choose a DSD JSON of pre-v1.1 format.
        """

        fdialog = QFileDialog()
        fdialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        fdialog.setNameFilters([self.tr("DSD File (*.json)")])
        fdialog.setWindowTitle(self.tr("Import pre-v1.1 Translation..."))

        if fdialog.exec() == QFileDialog.DialogCode.Rejected:
            return

        selected_files = fdialog.selectedFiles()

        if len(selected_files):
            filepath = Path(selected_files.pop(0))
            if not filepath.is_file():
                return

            self.__editor.import_legacy_dsd_translation(filepath)

    def __edit_string(self, string: Optional[String] = None) -> None:
        """
        Opens a string in a translator dialog.

        Args:
            string (Optional[String]): String to open. Defaults to the current string.
        """

        if string is None:
            string = self.__strings_widget.get_current_string()

        if string is not None:
            assert string.id in [s.id for s in self.__editor.all_strings]

            dialog = TranslatorDialog(
                self,
                string,
                self.app_config,
                self.user_data.user_config,
                self.translator,
            )
            dialog.update_signal.connect(self.update)
            dialog.show()

    def update_matching_strings(self, original: str, translation: str) -> None:
        """
        Update strings that are matching
        """

        self.__editor.apply_to_matching_strings(original, translation)

    def get_string_states_summary(self) -> dict[StringStatus, int]:
        """
        Get a summary of string states.

        Returns:
            dict[StringStatus, int]:
                Dictionary of string states and number of strings in each state
        """

        return {
            state: len(
                [
                    string
                    for string in self.__editor.all_strings
                    if string.status == state
                ]
            )
            for state in StringStatus
        }

    def get_visible_string_count(self) -> int:
        """
        Gets the number of visible strings.

        Returns:
            int: Number of visible strings
        """

        count: int = self.__strings_widget.get_visible_string_count()
        return count

    def get_index(self, string: String) -> int:
        """
        Gets the index of a string in the list.

        Args:
            string (String): The string to get the index of.

        Returns:
            int: The index
        """

        index: int = self.__strings_widget.get_index_of_string(
            string, only_visible=True
        )
        return index

    def get_string(self, index: int) -> Optional[String]:
        """
        Gets a string from an index.

        Args:
            index (int): The index.

        Returns:
            Optional[String]: The string or None if not found.
        """

        string: Optional[String] = self.__strings_widget.get_string_from_index(
            index, only_visible=True
        )
        return string

    @override
    def update(self) -> None:  # type: ignore
        """
        Updates visible string list.
        """

        self.__strings_widget.update()

        if self.__editor.changes_pending:
            self.__title_label.setText(self.translation.name + "*")
        else:
            self.__title_label.setText(self.translation.name)

        summary: dict[StringStatus, int] = self.get_string_states_summary()

        self.__strings_num_label.display(self.get_visible_string_count())
        self.__bar_chart.setValues(list(summary.values()))

        num_tooltip = ""

        for status, count in summary.items():
            color: Optional[QColor] = StringStatus.get_color(status)

            if color is None:
                num_tooltip += f"<tr><td>{status.get_localized_name()}:\
                    </td><td align=right>{count}</td></tr>"
            else:
                num_tooltip += f"<tr><td><font color='{color.name()}'>{status.get_localized_name()}:\
                    </font></td><td align=right><font color='{color.name()}'>{count}</font></td></tr>"

        self.__strings_num_label.setToolTip(num_tooltip)
        self.__bar_chart.setToolTip(num_tooltip)

    def __save(self) -> None:
        """
        Saves translation.
        """

        self.__editor.save()
        self.update()

    def __apply_database(self) -> None:
        """
        Applies database to untranslated strings.
        """

        modified_strings: int = self.__editor.apply_database(
            self.__strings_widget.get_selected_strings()
        )

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

    def __search_and_replace(self) -> None:
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
                self.__strings_widget.get_selected_strings(),
                replace_entry.text(),
                pattern,
            )

    def __translate_with_api(self) -> None:
        """
        Opens dialog to configure batch translation via user configured API.
        """

        if self.user_data.translator_config.show_confirmation_dialogs:
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
                    len(self.__strings_widget.get_selected_strings()),
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
                    self.user_data.translator_config.show_confirmation_dialogs = False
                    self.user_data.translator_config.save()
            else:
                return

        LoadingDialog.run_callable(
            QApplication.activeModalWidget(),
            lambda ldialog: self.__editor.translate_with_api(
                self.__strings_widget.get_selected_strings(), ldialog
            ),
        )

    def __export(self) -> None:
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

            Exporter.export_translation_dsd(self.translation, folder_path)

            messagebox = QMessageBox(QApplication.activeModalWidget())
            messagebox.setWindowTitle(self.tr("Success!"))
            messagebox.setText(self.tr("Translation successfully exported."))
            messagebox.exec()

    def __show_help(self) -> None:
        """
        Displays help popup.
        """

        EditorHelpDialog(QApplication.activeModalWidget()).exec()

    def __set_status(self, status: StringStatus) -> None:
        selected_items: StringList = self.__strings_widget.get_selected_strings()
        self.__editor.set_status(selected_items, status)

    def __reset_selected(self) -> None:
        selected_items: StringList = self.__strings_widget.get_selected_strings()

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

        # Reapply stylesheet as setDefaultButton() doesn't update the style by itself
        message_box.setStyleSheet(ThemeManager.get_stylesheet() or "")

        if message_box.exec() == QMessageBox.StandardButton.Yes:
            self.__editor.reset_strings(selected_items)

    def __copy_selected(self) -> None:
        """
        Copies current selected strings to clipboard.
        """

        selected_strings: StringList = self.__strings_widget.get_selected_strings()

        clipboard_text = ""
        for string in selected_strings:
            if isinstance(string, PluginString):
                clipboard_text += f"{string.type}\t"
                clipboard_text += f"{string.form_id}\t"
                clipboard_text += f"{string.editor_id}\t"
            clipboard_text += f"{string.original}\t"
            clipboard_text += f"{string.string}"
            clipboard_text += "\n"

        QApplication.clipboard().setText(clipboard_text.strip())

    def set_name_filter(self, name_filter: str, case_sensitive: bool) -> None:
        """
        Sets the name filter.

        Args:
            name_filter (str): The name to filter by.
            case_sensitive (bool): Case sensitivity.
        """

        self.__strings_widget.set_name_filter(name_filter, case_sensitive)
        self.update()

    def set_state_filter(self, state_filter: list[StringStatus]) -> None:
        """
        Sets the state filter.

        Args:
            state_filter (list[StringStatus]): The states to filter by.
        """

        self.__strings_widget.set_state_filter(state_filter)
        self.update()

    def go_to_modfile(self, modfile: Path) -> None:
        """
        Selects and scrolls to a specified mod file item.

        Args:
            modfile (Path):
                The path of the mod file, relative to the game's "Data" folder.
        """

        self.__strings_widget.go_to_modfile(modfile)

    def collapseAll(self) -> None:
        self.__strings_widget.collapseAll()

    def expandAll(self) -> None:
        self.__strings_widget.expandAll()
