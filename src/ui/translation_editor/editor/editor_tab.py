"""
Copyright (c) Cutleast
"""

import os
import re
from pathlib import Path
from typing import Optional

from cutleast_core_lib.core.utilities.typing_utils import not_none
from cutleast_core_lib.ui.progress.dialog import ProgressDialog
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.utilities.state_manager import WidgetStateManager
from cutleast_core_lib.ui.utilities.window_manager import WindowManager
from cutleast_core_lib.ui.widgets.elided_label import ElidedLabel
from cutleast_core_lib.ui.widgets.search_bar import SearchBar
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence, QShortcut
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
from core.string.string_status import StringStatus
from core.string.types import String, StringList
from core.translator.service import TranslatorService
from core.user_data.user_data import UserData
from ui.string_list.columns import StringsColumns
from ui.widgets.stacked_bar import StackedBar

from .editor_menu import EditorMenu
from .editor_toolbar import EditorToolbar
from .strings_widget import StringsWidget
from .translator_dialog import TranslatorDialog


class EditorTab(QWidget):
    """
    Class for editor tabs.
    """

    changed_signal = Signal()
    """
    This signal gets emitted when the tab has unsaved changes.
    """

    close_signal = Signal(Translation)
    """
    This signal gets emitted when tab is to be closed.
    """

    __editor: Editor

    __translation: Translation
    __app_config: AppConfig
    __user_data: UserData
    __translator_service: TranslatorService

    __vlayout: QVBoxLayout
    __title_label: QLabel
    __strings_num_label: QLabel
    __tool_bar: EditorToolbar
    __search_bar: SearchBar
    __bar_chart: StackedBar
    __menu: EditorMenu
    __strings_widget: StringsWidget

    __dialog: TranslatorDialog

    def __init__(
        self,
        translation: Translation,
        app_config: AppConfig,
        user_data: UserData,
        translator_service: TranslatorService,
    ) -> None:
        """
        Args:
            translation (Translation): The translation to edit.
            app_config (AppConfig): The application configuration.
            user_data (UserData): The user data.
            translator_service (TranslatorService): The translator service.
        """

        super().__init__()

        self.__translation = translation
        self.__app_config = app_config
        self.__user_data = user_data
        self.__translator_service = translator_service

        self.__editor = Editor(
            translation=translation,
            language=user_data.user_config.language,
            database=user_data.database,
            translator_service=translator_service,
        )
        self.__editor.strings_changed.connect(self.__on_strings_changed)

        self.__init_ui()
        self.__init_shortcuts()
        self.__init_dialog()

        self.__tool_bar.filter_changed.connect(self.__on_state_filter_changed)
        self.__tool_bar.apply_database_requested.connect(self.__apply_database)
        self.__tool_bar.search_and_replace_requested.connect(self.__search_and_replace)
        self.__tool_bar.api_translation_requested.connect(self.__translate_with_api)
        self.__tool_bar.save_requested.connect(self.__save)
        self.__tool_bar.export_requested.connect(self.__export)
        self.__search_bar.searchChanged.connect(self.__on_text_filter_changed)

        self.__strings_widget.itemSelectionChanged.connect(
            lambda: self.__tool_bar.set_edit_actions_enabled(
                len(self.__strings_widget.get_selected_strings()) > 0
            ),
        )
        self.__strings_widget.itemActivated.connect(
            lambda item, col: self.__edit_string()
        )
        self.__strings_widget.customContextMenuRequested.connect(
            lambda *_: self.__menu.open(
                bool(self.__strings_widget.get_selected_strings())
            )
        )
        self.__strings_widget.visible_string_count_changed.connect(
            self.__on_visible_string_count_changed
        )
        self.__strings_widget.order_changed.connect(self.__on_index_changed)

        self.__menu.expand_all_clicked.connect(self.__expand_all)
        self.__menu.collapse_all_clicked.connect(self.__collapse_all)
        self.__menu.edit_string_requested.connect(self.__edit_string)
        self.__menu.copy_string_requested.connect(self.__copy_selected)
        self.__menu.reset_translation_requested.connect(self.__reset_selected)
        self.__menu.mark_as_requested.connect(self.__set_status)

        self.__dialog.finalize_requested.connect(self.__on_finalize_requested)
        self.__dialog.prev_requested.connect(self.__on_prev_requested)
        self.__dialog.next_requested.connect(self.__on_next_requested)
        self.__dialog.api_translate_requested.connect(self.__on_api_translate_requested)

        ThemeManager.get().theme_changed.connect(lambda _: self.__update_metadata())

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.__vlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_strings_widget()
        self.__init_context_menu()
        self.__update_metadata()

    def __init_header(self) -> None:
        self.__tool_bar = EditorToolbar()
        self.__vlayout.addWidget(self.__tool_bar)

        first_action: QAction = self.__tool_bar.actions()[0]

        title_label = QLabel(self.tr("Translation Editor"))
        title_label.setProperty("title", True)
        self.__tool_bar.insertWidget(first_action, title_label)

        self.__title_label = ElidedLabel(self.__translation.name)
        self.__title_label.setMaximumWidth(300)
        self.__title_label.setProperty("subtitle", True)
        self.__tool_bar.insertWidget(first_action, self.__title_label)

        self.__tool_bar.insertSeparator(first_action)

        self.__search_bar = SearchBar()
        self.__tool_bar.addWidget(self.__search_bar)

        num_label = QLabel(self.tr("Strings") + ":")
        num_label.setProperty("subtitle", True)
        self.__tool_bar.addWidget(num_label)

        self.__strings_num_label = QLabel()
        self.__strings_num_label.setProperty("subtitle", True)
        self.__tool_bar.addWidget(self.__strings_num_label)

        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        self.__bar_chart = StackedBar(
            values=[0 for _ in StringStatus],
            colors=[s.get_base_color() for s in StringStatus],
        )
        self.__bar_chart.setFixedHeight(3)
        self.__vlayout.addWidget(self.__bar_chart)

    def __init_strings_widget(self) -> None:
        self.__strings_widget = StringsWidget(self.__editor.strings)
        self.__vlayout.addWidget(self.__strings_widget)

        WidgetStateManager.get().register_state(
            "editor_tab_strings_widget_header", self.__strings_widget.header()
        )

    def __init_context_menu(self) -> None:
        self.__menu = EditorMenu()

        self.__strings_widget.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )

    def __init_shortcuts(self) -> None:
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.__save)

        close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(
            lambda: self.close_signal.emit(self.__translation)
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

    def __init_dialog(self) -> None:
        self.__dialog = TranslatorDialog(
            spell_check_language=self.__user_data.user_config.language
            if self.__app_config.use_spell_check
            else None,
        )
        self.__dialog.set_strings_count(self.__strings_widget.get_visible_string_count())
        WidgetStateManager.get().register_geometry("translator_dialog", self.__dialog)

    @property
    def changes_pending(self) -> bool:
        """
        Whether there are unsaved changes.
        """

        return self.__editor.changes_pending

    def __edit_string(self, string: Optional[String] = None) -> None:
        """
        Opens a string in the translator dialog.

        Args:
            string (Optional[String]): String to open. Defaults to the current string.
        """

        if string is None:
            string = self.__strings_widget.get_current_string()

        if string is not None:
            assert string.id in [s.id for s in self.__editor.all_strings]

            self.__dialog.set_string(string)
            self.__dialog.set_index(self.__strings_widget.get_index_of_string(string))

            WindowManager.get().show(self.__dialog, delete_on_close=False)

    def __on_visible_string_count_changed(self, count: int) -> None:
        self.__dialog.set_strings_count(count)
        self.__on_index_changed()

    def __on_index_changed(self) -> None:
        current_string: Optional[String] = self.__dialog.current_string
        if current_string is not None:
            try:
                index: int = self.__strings_widget.get_index_of_string(
                    current_string, only_visible=True
                )
            except ValueError:
                self.__goto_index(0)
            else:
                self.__dialog.set_index(index)

    def __on_next_requested(self) -> None:
        current_string: Optional[String] = self.__dialog.current_string

        strings_count: int = self.__strings_widget.get_visible_string_count()
        if strings_count < 1:
            self.__dialog.finish()
            return

        current_index: int = -1
        if current_string is not None:
            try:
                current_index = self.__strings_widget.get_index_of_string(
                    current_string, only_visible=True
                )
            except ValueError:
                pass  # string was filtered out

        new_index: int
        if current_index == (strings_count - 1):
            new_index = 0
        else:
            new_index = current_index + 1

        self.__goto_index(new_index)

    def __on_prev_requested(self) -> None:
        current_string: Optional[String] = self.__dialog.current_string

        current_index: int = -1
        if current_string is not None:
            try:
                current_index = self.__strings_widget.get_index_of_string(
                    current_string, only_visible=True
                )
            except ValueError:
                pass  # string was filtered out

        strings_count: int = self.__strings_widget.get_visible_string_count()

        new_index: int
        if current_index > 0:
            new_index = current_index - 1
        else:
            new_index = strings_count - 1

        self.__goto_index(new_index)

    def __goto_index(self, index: int) -> None:
        string: Optional[String] = self.__strings_widget.get_string_from_index(
            index, only_visible=True
        )
        if string is None:
            self.__dialog.close()
            return

        self.__dialog.set_string(string)
        self.__dialog.set_index(index)

    def __on_strings_changed(self, changed_strings: StringList) -> None:
        for changed_string in changed_strings:
            self.__strings_widget.update_string(changed_string)

        self.__update_metadata()
        self.changed_signal.emit()

    def __update_metadata(self) -> None:
        if self.__editor.changes_pending:
            self.__title_label.setText(self.__translation.name + "*")
        else:
            self.__title_label.setText(self.__translation.name)

        visible_strings: StringList = self.__strings_widget.get_visible_strings()
        summary: dict[StringStatus, int] = self.__editor.get_string_states_summary(
            visible_strings
        )

        self.__strings_num_label.setText(str(len(visible_strings)))
        self.__bar_chart.setValues(list(summary.values()))
        self.__bar_chart.setColors([s.get_base_color() for s in StringStatus])

        num_tooltip = ""

        for status, count in summary.items():
            color: str = status.get_fg_color().name()

            num_tooltip += (
                f"<tr><td><font color='{color}'>{status.get_localized_name()}:"
                f"</font></td><td align=right><font color='{color}'>{count}"
                "</font></td></tr>"
            )

        self.__strings_num_label.setToolTip(num_tooltip)
        self.__bar_chart.setToolTip(num_tooltip)

    def __save(self) -> None:
        """
        Saves translation.
        """

        self.__editor.save()
        self.__update_metadata()
        self.changed_signal.emit()

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
                "Translated %n string from database.",
                "Translated %n strings from database.",
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

        case_sensitivity_checkbox = QCheckBox(self.tr("Case sensitive"))
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

        if self.__user_data.translator_config.show_confirmation_dialogs:
            dialog = QDialog(QApplication.activeModalWidget())
            dialog.setWindowTitle(self.tr("Translate with API"))

            vlayout = QVBoxLayout()
            dialog.setLayout(vlayout)

            label = QLabel(
                self.tr(
                    "Are you sure you want to translate %n string via translator API?\n"
                    "Depending on the translator API this can raise unexpected costs.",
                    "Are you sure you want to translate %n strings via translator API?\n"
                    "Depending on the translator API this can raise unexpected costs.",
                    len(self.__strings_widget.get_selected_strings()),
                )
            )
            vlayout.addWidget(label)

            vlayout.addStretch()

            hlayout = QHBoxLayout()
            vlayout.addLayout(hlayout)

            hlayout.addStretch()

            do_not_show_again_checkbox = QCheckBox(self.tr("Don't show again"))
            hlayout.addWidget(do_not_show_again_checkbox)

            confirm_button = QPushButton(self.tr("Continue"))
            confirm_button.clicked.connect(dialog.accept)
            confirm_button.setDefault(True)
            hlayout.addWidget(confirm_button)

            cancel_button = QPushButton(self.tr("Cancel"))
            cancel_button.clicked.connect(dialog.reject)
            hlayout.addWidget(cancel_button)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                if do_not_show_again_checkbox.isChecked():
                    self.__user_data.translator_config.show_confirmation_dialogs = False
                    self.__user_data.translator_config.save()
            else:
                return

        ProgressDialog(
            lambda pdisplay: self.__editor.translate_with_api(
                self.__strings_widget.get_selected_strings(), pdisplay
            ),
            QApplication.activeModalWidget(),
        ).run()

    def __export(self) -> None:
        """
        Exports translation in DSD format to a user selected path.
        """

        if self.__editor.changes_pending:
            message_box = QMessageBox(self)
            message_box.setWindowTitle(self.tr("Save before export?"))
            message_box.setText(
                self.tr(
                    "Do you want to save the translation before exporting? Unsaved "
                    "changes are not exported."
                )
            )
            message_box.setStandardButtons(
                QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(QMessageBox.StandardButton.Yes)
            message_box.button(QMessageBox.StandardButton.No).setText(
                self.tr("Export only")
            )
            message_box.button(QMessageBox.StandardButton.Yes).setText(
                self.tr("Save and export")
            )
            ThemeManager.update_widget_styles(message_box)

            if message_box.exec() == QMessageBox.StandardButton.Yes:
                self.__save()

        file_dialog = QFileDialog(QApplication.activeModalWidget())
        file_dialog.setWindowTitle(self.tr("Export Translation (DSD Format only)"))
        file_dialog.setFileMode(QFileDialog.FileMode.Directory)

        if file_dialog.exec():
            folder = file_dialog.selectedFiles()[0]
            folder = os.path.normpath(folder)
            folder_path = Path(folder)

            Exporter.export_translation(
                self.__translation, self.__user_data.mod_instance, folder_path
            )

            messagebox = QMessageBox(QApplication.activeModalWidget())
            messagebox.setWindowTitle(self.tr("Success!"))
            messagebox.setText(self.tr("Translation successfully exported."))
            messagebox.exec()

    def __set_status(self, status: StringStatus) -> None:
        selected_items: StringList = self.__strings_widget.get_selected_strings()
        self.__editor.set_status(selected_items, status)

    def __reset_selected(self) -> None:
        selected_items: StringList = self.__strings_widget.get_selected_strings()

        if not selected_items:
            return

        message_box = QMessageBox(QApplication.activeModalWidget())
        message_box.setWindowTitle(self.tr("Reset selected String(s)"))
        message_box.setText(
            self.tr("Are you sure you want to reset the selected string(s)?")
        )
        message_box.setStandardButtons(
            QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes
        )
        message_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        message_box.button(QMessageBox.StandardButton.No).setText(self.tr("No"))
        message_box.button(QMessageBox.StandardButton.Yes).setText(self.tr("Yes"))
        ThemeManager.update_widget_styles(message_box)

        if message_box.exec() == QMessageBox.StandardButton.Yes:
            self.__editor.reset_strings(selected_items)

    def __copy_selected(self) -> None:
        selected_strings: StringList = self.__strings_widget.get_selected_strings()

        clipboard_text = ""
        for string in selected_strings:
            for col in StringsColumns.get_columns(type(string)):
                clipboard_text += col.get_copy_text(string) + "\t"

            clipboard_text = clipboard_text.rstrip("\t")
            clipboard_text += "\n"

        QApplication.clipboard().setText(clipboard_text.rstrip("\n"))

    def __on_text_filter_changed(self, name_filter: str, case_sensitive: bool) -> None:
        self.__strings_widget.set_name_filter(name_filter, case_sensitive)
        self.__update_metadata()

    def __on_state_filter_changed(self, state_filter: list[StringStatus]) -> None:
        self.__strings_widget.set_state_filter(state_filter)
        self.__update_metadata()

    def __on_finalize_requested(
        self, translated_text: str, status: StringStatus
    ) -> None:
        current_string: String = not_none(self.__dialog.current_string)
        self.__editor.finalize_string(current_string, translated_text, status)

    def __on_api_translate_requested(self) -> None:
        current_string: Optional[String] = self.__dialog.current_string
        if current_string is None:
            return

        translated_text: str = self.__editor.get_api_translation(current_string)
        self.__dialog.set_translated_text(translated_text)

    def go_to_modfile(self, modfile: Path) -> None:
        """
        Selects and scrolls to a specified mod file item.

        Args:
            modfile (Path):
                The path of the mod file, relative to the game's "Data" folder.
        """

        self.__strings_widget.go_to_modfile(modfile)

    def __collapse_all(self) -> None:
        self.__strings_widget.collapseAll()

    def __expand_all(self) -> None:
        self.__strings_widget.expandAll()
