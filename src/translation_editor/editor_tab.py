"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import os
import re
from copy import copy
from pathlib import Path

import jstyleson as json
import pyperclip
import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import utilities as utils
from database import Translation
from main import MainApp
from widgets import LoadingDialog, SearchBar, StackedBar


class EditorTab(qtw.QWidget):
    """
    Class for editor tabs.
    """

    changes_pending: bool = False
    changes_signal = qtc.Signal()

    items: dict[qtw.QTreeWidgetItem, utils.String] = None
    plugins: dict[str, list[utils.String]] = None

    log = logging.getLogger("TranslationEditor")

    def __init__(self, app: MainApp, translation: Translation, plugin_name: str = None):
        super().__init__()

        def on_change():
            self.changes_pending = True

        self.changes_signal.connect(on_change)

        self.app = app
        self.loc = app.loc
        self.mloc = app.loc.editor
        self.translation = translation
        self.plugin_name = plugin_name

        save_shortcut = qtg.QShortcut(qtg.QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save)

        close_shortcut = qtg.QShortcut(qtg.QKeySequence("Ctrl+W"), self)
        close_shortcut.activated.connect(
            lambda: app.translation_editor.close_translation(translation)
        )

        vlayout = qtw.QVBoxLayout()
        self.setLayout(vlayout)

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.title_label = qtw.QLabel(
            f"{translation.name} > {plugin_name}" if plugin_name else translation.name
        )
        self.title_label.setObjectName("relevant_label")
        self.changes_signal.connect(
            lambda: self.title_label.setText(
                f"{self.translation.name} > {self.plugin_name}*"
                if self.plugin_name
                else self.translation.name + "*"
            )
        )
        hlayout.addWidget(self.title_label)

        hlayout.addStretch()

        num_label = qtw.QLabel(self.mloc.strings + ":")
        num_label.setObjectName("relevant_label")
        hlayout.addWidget(num_label)

        self.strings_num_label = qtw.QLCDNumber()
        self.strings_num_label.setDigitCount(6)
        hlayout.addWidget(self.strings_num_label)

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.tool_bar = qtw.QToolBar()
        self.tool_bar.setIconSize(qtc.QSize(32, 32))
        self.tool_bar.setFloatable(False)
        hlayout.addWidget(self.tool_bar)

        filter_menu = qtw.QMenu()

        self.filter_no_translation_required = qtw.QCheckBox(
            self.mloc.filter_no_translation_required, filter_menu
        )
        self.filter_no_translation_required.setObjectName("menu_checkbox")
        self.filter_no_translation_required.setChecked(True)
        self.filter_no_translation_required.stateChanged.connect(
            lambda _: self.update_string_list()
        )
        widget_action = qtw.QWidgetAction(filter_menu)
        widget_action.setDefaultWidget(self.filter_no_translation_required)
        filter_menu.addAction(widget_action)

        self.filter_translation_complete = qtw.QCheckBox(
            self.mloc.filter_translation_complete, filter_menu
        )
        self.filter_translation_complete.setObjectName("menu_checkbox")
        self.filter_translation_complete.setChecked(True)
        self.filter_translation_complete.stateChanged.connect(
            lambda _: self.update_string_list()
        )
        widget_action = qtw.QWidgetAction(filter_menu)
        widget_action.setDefaultWidget(self.filter_translation_complete)
        filter_menu.addAction(widget_action)

        self.filter_translation_incomplete = qtw.QCheckBox(
            self.mloc.filter_translation_incomplete, filter_menu
        )
        self.filter_translation_incomplete.setObjectName("menu_checkbox")
        self.filter_translation_incomplete.setChecked(True)
        self.filter_translation_incomplete.stateChanged.connect(
            lambda _: self.update_string_list()
        )
        widget_action = qtw.QWidgetAction(filter_menu)
        widget_action.setDefaultWidget(self.filter_translation_incomplete)
        filter_menu.addAction(widget_action)

        self.filter_translation_required = qtw.QCheckBox(
            self.mloc.filter_translation_required, filter_menu
        )
        self.filter_translation_required.setObjectName("menu_checkbox")
        self.filter_translation_required.setChecked(True)
        self.filter_translation_required.stateChanged.connect(
            lambda _: self.update_string_list()
        )
        widget_action = qtw.QWidgetAction(filter_menu)
        widget_action.setDefaultWidget(self.filter_translation_required)
        filter_menu.addAction(widget_action)

        filter_action = self.tool_bar.addAction(
            qta.icon("mdi6.filter", color="#ffffff"),
            self.loc.main.filter_options,
        )
        filter_action.setMenu(filter_menu)
        filter_action.triggered.connect(
            lambda: filter_menu.exec(self.tool_bar.mapToGlobal(self.tool_bar.pos()))
        )
        self.tool_bar.addAction(filter_action)

        help_action = self.tool_bar.addAction(
            qta.icon("mdi6.help", color="#ffffff"), self.mloc.show_help
        )
        help_action.triggered.connect(self.show_help)

        self.tool_bar.addSeparator()

        import_legacy_action = self.tool_bar.addAction(
            qta.icon("ri.inbox-archive-fill", color="#ffffff"),
            self.mloc.import_legacy,
        )
        import_legacy_action.triggered.connect(self.import_legacy)

        apply_database_action = self.tool_bar.addAction(
            qta.icon("mdi6.database-refresh-outline", color="#ffffff"),
            self.mloc.apply_database,
        )
        apply_database_action.triggered.connect(self.apply_database)

        replacer_action = self.tool_bar.addAction(
            qta.icon("msc.replace", color="#ffffff"),
            self.mloc.search_and_replace,
        )
        replacer_action.triggered.connect(self.search_and_replace)
        replacer_action.setDisabled(True)

        translate_with_api_action = self.tool_bar.addAction(
            qta.icon("ri.translate", color="#ffffff"),
            self.mloc.translate_with_api,
        )
        translate_with_api_action.triggered.connect(self.translate_with_api)
        translate_with_api_action.setDisabled(True)

        self.tool_bar.addSeparator()

        save_action = self.tool_bar.addAction(
            qta.icon("fa5s.save", color="#ffffff"), self.loc.main.save
        )
        save_action.triggered.connect(self.save)

        export_action = self.tool_bar.addAction(
            qta.icon("fa5s.share", color="#ffffff"),
            self.loc.database.export_translation,
        )
        export_action.triggered.connect(self.export)

        self.search_bar = SearchBar()
        self.search_bar.setPlaceholderText(self.loc.main.search)
        self.search_bar.cs_toggle.setToolTip(self.loc.main.case_sensitivity)
        self.search_bar.textChanged.connect(lambda text: self.update_string_list())
        hlayout.addWidget(self.search_bar)

        self.bar_chart = StackedBar(
            [0 for s in utils.String.Status.get_members()],
            colors=[
                utils.String.Status.get_color(s)
                for s in utils.String.Status.get_members()
            ],
        )
        self.bar_chart.setFixedHeight(3)
        vlayout.addWidget(self.bar_chart)

        self.strings_widget = qtw.QTreeWidget()
        self.strings_widget.itemSelectionChanged.connect(
            lambda: (
                replacer_action.setEnabled(bool(self.strings_widget.selectedItems())),
                translate_with_api_action.setEnabled(
                    bool(self.strings_widget.selectedItems())
                ),
            ),
        )
        self.strings_widget.setAlternatingRowColors(True)
        self.strings_widget.setSelectionMode(
            qtw.QTreeWidget.SelectionMode.ExtendedSelection
        )
        self.strings_widget.setUniformRowHeights(True)
        self.strings_widget.header().setSortIndicatorClearable(True)
        self.strings_widget.header().setFirstSectionMovable(True)
        self.strings_widget.setIndentation(0)
        self.strings_widget.setSortingEnabled(True)
        vlayout.addWidget(self.strings_widget)

        self.strings_widget.setHeaderLabels(
            [
                self.loc.main.type,
                self.loc.main.form_id,
                self.loc.main.editor_id,
                self.loc.main.original,
                self.loc.main.string,
            ]
        )

        translation.load_translation()

        self.items = {}
        self.plugins = {}
        if plugin_name:
            self.plugins[plugin_name] = []
            for string in translation.strings[plugin_name]:
                item = qtw.QTreeWidgetItem(
                    [
                        string.type,
                        string.form_id if string.form_id is not None else "",
                        string.editor_id if string.editor_id is not None else "",
                        utils.trim_string(string.original_string),
                        utils.trim_string(string.translated_string),
                    ]
                )

                item.setFont(0, qtg.QFont("Consolas"))
                item.setFont(1, qtg.QFont("Consolas"))
                item.setFont(2, qtg.QFont("Consolas"))

                # Create copy of string to prevent unwanted changes to original string
                string = copy(string)
                self.items[item] = string
                self.plugins[plugin_name].append(string)

                self.strings_widget.addTopLevelItem(item)
        else:
            for plugin_name, strings in translation.strings.items():
                self.plugins[plugin_name] = []
                for string in strings:
                    item = qtw.QTreeWidgetItem(
                        [
                            string.type,
                            string.form_id if string.form_id is not None else "",
                            string.editor_id if string.editor_id is not None else "",
                            utils.trim_string(string.original_string),
                            utils.trim_string(string.translated_string),
                        ]
                    )

                    item.setFont(0, qtg.QFont("Consolas"))
                    item.setFont(1, qtg.QFont("Consolas"))
                    item.setFont(2, qtg.QFont("Consolas"))

                    # Create copy of string to prevent unwanted changes to original string
                    string = copy(string)
                    self.items[item] = string
                    self.plugins[plugin_name].append(string)

                    self.strings_widget.addTopLevelItem(item)

        self.update_string_list()

        self.strings_widget.header().setDefaultSectionSize(200)
        self.strings_widget.resizeColumnToContents(0)
        self.strings_widget.resizeColumnToContents(1)
        self.strings_widget.header().resizeSection(3, 400)

        self.strings_widget.itemActivated.connect(self.open_translator_dialog)

        complete_shortcut = qtg.QShortcut(qtg.QKeySequence("F1"), self)
        incomplete_shortcut = qtg.QShortcut(qtg.QKeySequence("F2"), self)
        no_required_shortcut = qtg.QShortcut(qtg.QKeySequence("F3"), self)
        reset_shortcut = qtg.QShortcut(qtg.QKeySequence("F4"), self)

        complete_shortcut.activated.connect(
            lambda: self.set_status(utils.String.Status.TranslationComplete)
        )

        incomplete_shortcut.activated.connect(
            lambda: self.set_status(utils.String.Status.TranslationIncomplete)
        )

        no_required_shortcut.activated.connect(
            lambda: self.set_status(utils.String.Status.NoTranslationRequired)
        )

        reset_shortcut.activated.connect(self.reset_translation)

        def on_context_menu(point: qtc.QPoint):
            if not self.strings_widget.selectedItems():
                return

            # Get item at mouse position minus header height
            mouse_pos = self.strings_widget.mapFromGlobal(qtg.QCursor.pos())
            mouse_pos.setY(mouse_pos.y() - self.strings_widget.header().height())
            current_item = self.strings_widget.itemAt(mouse_pos)

            def open_translator():
                self.open_translator_dialog(current_item, 0)

            menu = qtw.QMenu()

            open_translator_action = menu.addAction(self.mloc.open_translator)
            open_translator_action.setIcon(qta.icon("mdi6.rename", color="#ffffff"))
            open_translator_action.triggered.connect(open_translator)

            copy_action = menu.addAction(self.loc.main.copy)
            copy_action.setIcon(qta.icon("mdi6.content-copy", color="#ffffff"))
            copy_action.setIconVisibleInMenu(True)
            copy_action.triggered.connect(self.copy_selected)

            reset_translation_action = menu.addAction(self.mloc.reset_translation)
            reset_translation_action.setIcon(
                qta.icon("ri.arrow-go-back-line", color="#ffffff")
            )
            reset_translation_action.setShortcut(qtg.QKeySequence("F4"))
            reset_translation_action.triggered.connect(self.reset_translation)

            menu.addSeparator()

            no_translation_required_action = menu.addAction(
                f'{self.mloc.mark_as} "{self.mloc.no_translation_required_status}"'
            )
            no_translation_required_action.setIcon(
                qta.icon(
                    "mdi6.square-rounded",
                    color=utils.String.Status.get_color(
                        utils.String.Status.NoTranslationRequired
                    ),
                )
            )
            no_translation_required_action.setShortcut(qtg.QKeySequence("F3"))
            no_translation_required_action.triggered.connect(
                lambda: self.set_status(utils.String.Status.NoTranslationRequired)
            )

            translation_complete_action = menu.addAction(
                f'{self.mloc.mark_as} "{self.mloc.translation_complete_status}"'
            )
            translation_complete_action.setIcon(
                qta.icon(
                    "mdi6.square-rounded",
                    color=utils.String.Status.get_color(
                        utils.String.Status.TranslationComplete
                    ),
                )
            )
            translation_complete_action.setShortcut(qtg.QKeySequence("F1"))
            translation_complete_action.triggered.connect(
                lambda: self.set_status(utils.String.Status.TranslationComplete)
            )

            translation_incomplete_action = menu.addAction(
                f'{self.mloc.mark_as} "{self.mloc.translation_incomplete_status}"'
            )
            translation_incomplete_action.setIcon(
                qta.icon(
                    "mdi6.square-rounded",
                    color=utils.String.Status.get_color(
                        utils.String.Status.TranslationIncomplete
                    ),
                )
            )
            translation_incomplete_action.setShortcut(qtg.QKeySequence("F2"))
            translation_incomplete_action.triggered.connect(
                lambda: self.set_status(utils.String.Status.TranslationIncomplete)
            )

            translation_required_action_action = menu.addAction(
                f'{self.mloc.mark_as} "{self.mloc.translation_required_status}"'
            )
            translation_required_action_action.setIcon(
                qta.icon(
                    "mdi6.square-rounded",
                    color=utils.String.Status.get_color(
                        utils.String.Status.TranslationRequired
                    ),
                )
            )
            translation_required_action_action.triggered.connect(
                lambda: self.set_status(utils.String.Status.TranslationRequired)
            )

            menu.exec(self.strings_widget.mapToGlobal(point), at=open_translator_action)

        self.strings_widget.setContextMenuPolicy(
            qtc.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.strings_widget.customContextMenuRequested.connect(on_context_menu)

    def import_legacy(self):
        """
        Opens file dialog to choose a DSD JSON of pre-v1.1 format.
        """

        fdialog = qtw.QFileDialog()
        fdialog.setFileMode(fdialog.FileMode.ExistingFile)
        fdialog.setNameFilters(["DSD File (*.json)"])
        fdialog.setWindowTitle(self.mloc.import_legacy)

        if fdialog.exec() == fdialog.DialogCode.Rejected:
            return

        selected_files = fdialog.selectedFiles()

        if len(selected_files):
            filepath = Path(selected_files[0])
            if not filepath.is_file():
                return

            self.log.info(f"Importing legacy translation from {str(filepath)!r}...")

            with filepath.open(encoding="utf8") as file:
                legacy_strings: list[dict] = json.load(file)

            self.log.debug(
                f"Found {len(legacy_strings)} string(s) in legacy translation."
            )

            translation_strings: dict[str, list[utils.String]] = {}

            for string in self.items.values():
                if string.original_string in translation_strings:
                    translation_strings[string.original_string].append(string)
                else:
                    translation_strings[string.original_string] = [string]

            applied = 0

            for legacy_string in legacy_strings:
                original = legacy_string.get("original")
                translated = legacy_string.get("string")

                if original is None or translated is None:
                    continue

                matching_strings = translation_strings.get(original)

                if matching_strings is None:
                    continue

                for matching_string in matching_strings:
                    matching_string.translated_string = translated

                    for item, string in self.items.items():
                        if string == matching_string:
                            item.setText(4, utils.trim_string(translated))

                    if (
                        legacy_string.get("type") == matching_string.type
                        and legacy_string.get("editor_id") == matching_string.editor_id
                        and legacy_string.get("index") == matching_string.index
                    ):
                        legacy_status = utils.String.Status.get(
                            legacy_string.get("status")
                        )

                        if legacy_status is not None:
                            matching_string.status = legacy_status
                        else:
                            matching_string.status = (
                                utils.String.Status.TranslationComplete
                            )

                applied += 1

            if applied:
                self.update_string_list()

            self.log.info(f"Translated {applied} string(s) from legacy translation.")

    def open_translator_dialog(self, item: qtw.QTreeWidgetItem, column: int):
        """
        Opens double clicked string in popup.
        """

        from .translator_dialog import TranslatorDialog

        self.current_translation_index = self.strings_widget.indexOfTopLevelItem(item)

        dialog = TranslatorDialog(self, item)
        dialog.show()
        dialog.string_entry.setFocus()

    def update_matching_strings(self, original: str, translation: str):
        """
        Update strings that are matching
        """

        for tree_item, string in self.items.items():
            if string.original_string == original:
                if string.status != string.Status.TranslationComplete:
                    string.translated_string = translation
                    tree_item.setText(4, utils.trim_string(string.translated_string))
                    string.status = string.Status.TranslationComplete

        self.update_string_list()
        self.changes_signal.emit()

    def update_string_list(self):
        """
        Updates visible string list.
        """

        cur_search = self.search_bar.text()
        case_sensitive = self.search_bar.cs_toggle.isChecked()

        no_translation_required_strings = 0
        translation_complete_strings = 0
        translation_incomplete_strings = 0
        translation_required_strings = 0

        for tree_item, string in self.items.items():
            string_text = string.type + string.original_string
            if string.form_id is not None:
                string_text += string.form_id
            if string.editor_id is not None:
                string_text += string.editor_id
            if string.translated_string is not None:
                string_text += string.translated_string

            if case_sensitive:
                string_visible = cur_search in string_text
            else:
                string_visible = cur_search.lower() in string_text.lower()

            if string_visible:
                match string.status:
                    case string.Status.NoTranslationRequired:
                        string_visible = self.filter_no_translation_required.isChecked()
                    case string.Status.TranslationComplete:
                        string_visible = self.filter_translation_complete.isChecked()
                    case string.Status.TranslationIncomplete:
                        string_visible = self.filter_translation_incomplete.isChecked()
                    case string.Status.TranslationRequired:
                        string_visible = self.filter_translation_required.isChecked()

            # If string is still visible, increase resp. counter
            if string_visible:
                match string.status:
                    case string.Status.NoTranslationRequired:
                        no_translation_required_strings += 1
                    case string.Status.TranslationComplete:
                        translation_complete_strings += 1
                    case string.Status.TranslationIncomplete:
                        translation_incomplete_strings += 1
                    case string.Status.TranslationRequired:
                        translation_required_strings += 1

            tree_item.setToolTip(0, string.type)
            if string.form_id is not None:
                tree_item.setToolTip(1, string.form_id)
            if string.editor_id is not None:
                tree_item.setToolTip(2, string.editor_id)
            tree_item.setToolTip(3, string.original_string)
            tree_item.setToolTip(4, string.translated_string)

            for c in range(5):
                tree_item.setForeground(c, string.Status.get_color(string.status))

            tree_item.setHidden(not string_visible)

        self.strings_num_label.display(
            no_translation_required_strings
            + translation_complete_strings
            + translation_incomplete_strings
            + translation_required_strings
        )

        self.bar_chart.setValues(
            [
                no_translation_required_strings,
                translation_complete_strings,
                translation_incomplete_strings,
                translation_required_strings,
            ]
        )

        num_tooltip = f"""
<table cellspacing="5">
<tr><td><font color="{utils.String.Status.get_color(
    utils.String.Status.NoTranslationRequired
).name()}">{self.mloc.no_translation_required_status}:\
</font></td><td align=right><font color="{utils.String.Status.get_color(
    utils.String.Status.NoTranslationRequired
).name()}">{no_translation_required_strings}</font></td></tr>

<tr><td><font color="{utils.String.Status.get_color(
    utils.String.Status.TranslationComplete
).name()}">{self.mloc.translation_complete_status}:\
</font></td><td align=right><font color="{utils.String.Status.get_color(
    utils.String.Status.TranslationComplete
).name()}">{translation_complete_strings}</font></td></tr>

<tr><td><font color="{utils.String.Status.get_color(
    utils.String.Status.TranslationIncomplete
).name()}">{self.mloc.translation_incomplete_status}:\
</font></td><td align=right><font color="{utils.String.Status.get_color(
    utils.String.Status.TranslationIncomplete
).name()}">{translation_incomplete_strings}</font></td></tr>

<tr><td><font color="{utils.String.Status.get_color(
    utils.String.Status.TranslationRequired
).name()}">{self.mloc.translation_required_status}:\
</font></td><td align=right><font color="{utils.String.Status.get_color(
    utils.String.Status.TranslationRequired
).name()}">{translation_required_strings}</font></td></tr>

</table>
"""
        self.strings_num_label.setToolTip(num_tooltip)
        self.bar_chart.setToolTip(num_tooltip)

        if self.strings_widget.selectedItems():
            self.strings_widget.scrollToItem(
                self.strings_widget.selectedItems()[0],
                qtw.QTreeWidget.ScrollHint.PositionAtCenter,
            )

    def save(self):
        """
        Saves translation.
        """

        self.log.info(f"Saving Translation {self.translation.name!r}...")

        for plugin_name, strings in self.plugins.items():
            self.translation.strings[plugin_name] = strings
        self.translation.save_translation()
        self.changes_pending = False

        self.title_label.setText(
            f"{self.translation.name} > {self.plugin_name}"
            if self.plugin_name
            else self.translation.name
        )

        # Get tree item belonging to this tab
        item = list(self.app.translation_editor.tabs)[
            list(self.app.translation_editor.tabs.values()).index(self)
        ]
        item.setText(0, self.plugin_name or self.translation.name)

        self.log.info("Translation saved.")

    def apply_database(self):
        """
        Applies database to untranslated strings.
        """

        self.log.info(f"Applying database to {len(self.items)} string(s)...")

        pre_translated_strings = len(
            [
                string
                for string in self.items.values()
                if string.status == string.Status.TranslationComplete
                or string.status == string.Status.TranslationIncomplete
            ]
        )

        def process(ldialog: LoadingDialog):
            ldialog.updateProgress(text1=self.mloc.applying_database)

            self.app.database.apply_db_to_translation(
                self.translation, self.plugin_name
            )

        loadingdialog = LoadingDialog(self.app.root, self.app, process)
        loadingdialog.exec()

        newly_translated_strings = len(
            [
                string
                for string in self.items.values()
                if string.status == string.Status.TranslationComplete
                or string.status == string.Status.TranslationIncomplete
            ]
        )
        newly_translated_strings -= pre_translated_strings

        self.update_string_list()
        if newly_translated_strings:
            self.changes_signal.emit()

        self.log.info(
            f"Database successfully applied to {newly_translated_strings} string(s)."
        )

        messagebox = qtw.QMessageBox(self.app.root)
        messagebox.setWindowTitle(self.loc.main.success)
        messagebox.setText(
            self.mloc.database_translation_complete.replace(
                "[NUMBER]", str(newly_translated_strings)
            )
        )
        utils.apply_dark_title_bar(messagebox)
        messagebox.exec()

    def search_and_replace(self):
        """
        Opens dialog for advanced search and replace operations.
        """

        selected_strings = {
            string: tree_item
            for tree_item, string in self.items.items()
            if tree_item in self.strings_widget.selectedItems()
        }

        dialog = qtw.QDialog(self.app.root)
        dialog.setMinimumWidth(700)
        dialog.setWindowTitle(self.mloc.search_and_replace)
        utils.apply_dark_title_bar(dialog)

        vlayout = qtw.QVBoxLayout()
        dialog.setLayout(vlayout)

        flayout = qtw.QFormLayout()
        vlayout.addLayout(flayout)

        search_entry = qtw.QLineEdit()
        flayout.addRow(self.mloc.search, search_entry)

        replace_entry = qtw.QLineEdit()
        flayout.addRow(self.mloc.replace, replace_entry)

        case_sensitivity_checkbox = qtw.QCheckBox(self.loc.main.case_sensitivity)
        flayout.addRow(case_sensitivity_checkbox)

        vlayout.addStretch()

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        hlayout.addStretch()

        apply_button = qtw.QPushButton(self.loc.main.apply)

        def apply():
            for string, tree_item in selected_strings.items():
                old_string = string.translated_string

                if case_sensitivity_checkbox.isChecked():
                    string.translated_string = string.translated_string.replace(
                        search_entry.text(), replace_entry.text()
                    )
                else:
                    compiled = re.compile(re.escape(search_entry.text()), re.IGNORECASE)
                    res = compiled.sub(replace_entry.text(), string.translated_string)
                    string.translated_string = str(res)

                # Only set String to "TranslationIncomplete" if it was changed
                if old_string != string.translated_string:
                    tree_item.setText(4, utils.trim_string(string.translated_string))
                    string.status = string.Status.TranslationIncomplete

            self.update_string_list()
            self.changes_signal.emit()
            dialog.accept()

        apply_button.clicked.connect(apply)
        hlayout.addWidget(apply_button)

        cancel_button = qtw.QPushButton(self.loc.main.cancel)
        cancel_button.clicked.connect(dialog.accept)
        hlayout.addWidget(cancel_button)

        dialog.exec()

    def translate_with_api(self):
        """
        Opens dialog to configure batch translation via user configured API.
        """

        selected_strings = {
            string: tree_item
            for tree_item, string in self.items.items()
            if tree_item in self.strings_widget.selectedItems()
        }

        def _run():
            def process(ldialog: LoadingDialog):
                ldialog.updateProgress(text1=self.mloc.translating_with_api)

                texts = [
                    selected_string.original_string
                    for selected_string in selected_strings
                ]
                result = self.app.translator.mass_translate(
                    texts, "English", self.app.user_config["language"]
                )

                for string in selected_strings:
                    string.translated_string = result[string.original_string]
                    string.status = string.Status.TranslationIncomplete

            loadingdialog = LoadingDialog(self.app.root, self.app, process)
            loadingdialog.exec()

            for string, tree_item in selected_strings.items():
                tree_item.setText(4, utils.trim_string(string.translated_string))

            self.update_string_list()
            self.changes_signal.emit()

        if not self.app.translator_config.get("show_confirmation_dialogs", True):
            _run()
            return

        dialog = qtw.QDialog(self.app.root)
        dialog.setWindowTitle(self.mloc.translate_with_api)
        utils.apply_dark_title_bar(dialog)

        vlayout = qtw.QVBoxLayout()
        dialog.setLayout(vlayout)

        label = qtw.QLabel(
            self.mloc.api_translation_text.replace(
                "[NUMBER]", str(len(selected_strings))
            )
        )
        vlayout.addWidget(label)

        vlayout.addStretch()

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        hlayout.addStretch()

        apply_button = qtw.QPushButton(self.loc.main.apply)

        def apply():
            _run()

            if do_not_show_again_checkbox.isChecked():
                self.app.translator_config["show_confirmation_dialog"] = False
                with open(self.app.translator_conf_path, "w", encoding="utf8") as file:
                    json.dump(self.app.translator_config, file, indent=4)
            dialog.accept()

        apply_button.clicked.connect(apply)
        hlayout.addWidget(apply_button)

        cancel_button = qtw.QPushButton(self.loc.main.cancel)
        cancel_button.clicked.connect(dialog.accept)
        hlayout.addWidget(cancel_button)

        do_not_show_again_checkbox = qtw.QCheckBox(self.loc.main.do_not_show_again)
        hlayout.addWidget(do_not_show_again_checkbox)

        dialog.exec()

    def export(self):
        """
        Exports translation in DSD format to a user selected path.
        """

        file_dialog = qtw.QFileDialog(self.app.root)
        file_dialog.setWindowTitle(self.loc.database.export_translation)
        file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
        utils.apply_dark_title_bar(file_dialog)

        if file_dialog.exec():
            folder = file_dialog.selectedFiles()[0]
            folder = os.path.normpath(folder)
            folder = Path(folder)

            self.translation.export_translation(folder)

            messagebox = qtw.QMessageBox(self.app.root)
            messagebox.setWindowTitle(self.loc.main.success)
            messagebox.setText(self.loc.database.export_complete)
            utils.apply_dark_title_bar(messagebox)
            messagebox.exec()

    def show_help(self):
        """
        Displays help popup.
        """

        dialog = qtw.QDialog(self.app.root)
        dialog.setModal(True)
        dialog.setWindowTitle(self.loc.main.help)
        utils.apply_dark_title_bar(dialog)

        vlayout = qtw.QVBoxLayout()
        dialog.setLayout(vlayout)

        help_label = qtw.QLabel(self.mloc.help_text)
        help_label.setObjectName("relevant_label")
        help_label.setWordWrap(True)
        vlayout.addWidget(help_label)

        vlayout.addSpacing(25)

        flayout = qtw.QFormLayout()
        flayout.setAlignment(qtc.Qt.AlignmentFlag.AlignHCenter)
        flayout.setHorizontalSpacing(25)
        vlayout.addLayout(flayout)

        no_translation_required = qtw.QLabel()
        no_translation_required.setPixmap(
            qta.icon(
                "mdi6.square-rounded",
                color=utils.String.Status.get_color(
                    utils.String.Status.NoTranslationRequired
                ),
            ).pixmap(32, 32)
        )
        flayout.addRow(
            self.mloc.no_translation_required_status, no_translation_required
        )

        translation_complete = qtw.QLabel()
        translation_complete.setPixmap(
            qta.icon(
                "mdi6.square-rounded",
                color=utils.String.Status.get_color(
                    utils.String.Status.TranslationComplete
                ),
            ).pixmap(32, 32)
        )
        flayout.addRow(self.mloc.translation_complete_status, translation_complete)

        translation_incomplete = qtw.QLabel()
        translation_incomplete.setPixmap(
            qta.icon(
                "mdi6.square-rounded",
                color=utils.String.Status.get_color(
                    utils.String.Status.TranslationIncomplete
                ),
            ).pixmap(32, 32)
        )
        flayout.addRow(self.mloc.translation_incomplete_status, translation_incomplete)

        translation_required = qtw.QLabel()
        translation_required.setPixmap(
            qta.icon(
                "mdi6.square-rounded",
                color=utils.String.Status.get_color(
                    utils.String.Status.TranslationRequired
                ),
            ).pixmap(32, 32)
        )
        flayout.addRow(self.mloc.translation_required_status, translation_required)

        vlayout.addSpacing(25)

        ok_button = qtw.QPushButton(self.loc.main.ok)
        ok_button.clicked.connect(dialog.accept)
        vlayout.addWidget(ok_button)

        dialog.exec()

    def get_selected_items(self):
        return {
            tree_item: string
            for tree_item, string in self.items.items()
            if tree_item in self.strings_widget.selectedItems()
        }

    def set_status(self, status: utils.String.Status):
        selected_items = self.get_selected_items()

        for string in selected_items.values():
            string.status = status

        self.update_string_list()
        self.changes_signal.emit()

    def reset_translation(self):
        selected_items = self.get_selected_items()

        if not selected_items:
            return

        message_box = qtw.QMessageBox(self)
        utils.apply_dark_title_bar(message_box)
        message_box.setWindowTitle(self.mloc.reset_translation)
        message_box.setText(self.mloc.reset_translation_text)
        message_box.setStandardButtons(
            qtw.QMessageBox.StandardButton.No | qtw.QMessageBox.StandardButton.Yes
        )
        message_box.setDefaultButton(qtw.QMessageBox.StandardButton.Yes)
        message_box.button(qtw.QMessageBox.StandardButton.No).setText(self.loc.main.no)
        message_box.button(qtw.QMessageBox.StandardButton.Yes).setText(
            self.loc.main.yes
        )
        choice = message_box.exec()

        if choice == qtw.QMessageBox.StandardButton.Yes:
            for tree_item, string in selected_items.items():
                string.translated_string = string.original_string
                string.status = string.Status.TranslationRequired
                tree_item.setText(4, utils.trim_string(string.translated_string))

            self.update_string_list()
            self.changes_signal.emit()

    def copy_selected(self):
        """
        Copies current selected strings to clipboard.
        """

        selected_items = self.strings_widget.selectedItems()

        clipboard_text = ""
        for item in selected_items:
            for c in range(self.strings_widget.columnCount()):
                clipboard_text += f"{item.toolTip(c)!r}"[1:-1] + "\t"

            clipboard_text = clipboard_text.removesuffix("\t")
            clipboard_text += "\n"

        pyperclip.copy(clipboard_text.strip())

    def get_visible_strings(self):
        """
        Returns a list of strings that are visible with current filter.
        """

        return [
            string
            for tree_item, string in self.items.items()
            if not tree_item.isHidden()
        ]
