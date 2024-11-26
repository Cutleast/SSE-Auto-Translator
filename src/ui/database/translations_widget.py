"""
This file is part of SEE Auto Translator
and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os
import time
from pathlib import Path

import qtawesome as qta
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import (
    QCursor,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QIcon,
    QKeySequence,
    QShortcut,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLCDNumber,
    QLineEdit,
    QMenu,
    QMessageBox,
    QRadioButton,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app import MainApp
from core import plugin_interface
from core.database.translation import Translation
from core.translation_provider.file_download import FileDownload
from core.translation_provider.translation_download import TranslationDownload
from core.utilities import (
    apply_dark_title_bar,
    fmt_timestamp,
    get_folder_size,
    scale_value,
)
from core.utilities.importer import (
    import_from_archive,
    import_non_plugin_files,
    merge_plugin_strings,
)
from core.utilities.mod import Mod
from core.utilities.plugin import Plugin
from core.utilities.source import Source
from core.utilities.string import String
from ui.widgets.download_list_dialog import DownloadListDialog
from ui.widgets.error_dialog import ErrorDialog
from ui.widgets.loading_dialog import LoadingDialog
from ui.widgets.shortcut_button import ShortcutButton
from ui.widgets.string_list_dialog import StringListDialog


class TranslationsWidget(QWidget):
    """
    Tab for Translations Database.
    """

    def __init__(self, app: MainApp):
        super().__init__()

        self.app = app
        self.loc = app.loc
        self.mloc = app.loc.database

        self.setAcceptDrops(True)

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        hlayout = QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.tool_bar = QToolBar()
        hlayout.addWidget(self.tool_bar)

        show_vanilla_strings_action = self.tool_bar.addAction(
            qta.icon("mdi6.book-open-outline", color="#ffffff"),
            self.mloc.show_vanilla_strings,
        )

        def show_vanilla_strings():
            dialog = StringListDialog(
                self.app,
                "Base Game + AE CC Content",
                self.app.database.vanilla_translation.strings,
                show_translation=True,
            )
            dialog.show()

        show_vanilla_strings_action.triggered.connect(show_vanilla_strings)

        search_database_action = self.tool_bar.addAction(
            qta.icon("fa.search", color="#ffffff", scale_factor=0.85),
            self.mloc.search_database,
        )
        search_database_action.triggered.connect(self.search_database)

        self.tool_bar.addSeparator()

        local_import_button = self.tool_bar.addAction(
            qta.icon("mdi6.import", color="#ffffff"),
            self.mloc.import_local,
        )
        local_import_button.triggered.connect(self.import_local_translation)

        update_button = self.tool_bar.addAction(
            qta.icon("mdi6.cloud-refresh", color="#ffffff"),
            self.loc.main.check_for_updates,
        )
        update_button.triggered.connect(self.check_for_updates)

        self.download_updates_button = self.tool_bar.addAction(
            qta.icon("mdi6.cloud-download", color="#ffffff"),
            self.loc.updater.download_update,
        )
        self.download_updates_button.setDisabled(True)
        self.download_updates_button.triggered.connect(self.download_updates)

        def toggle_nxm():
            if self.nxmhandler_button.isChecked():
                self.app.nxm_listener.bind()
                self.app.log.info("Bound Nexus Mods Links.")
            else:
                self.app.nxm_listener.unbind()
                self.app.log.info("Unbound Nexus Mods Links.")

        self.nxmhandler_button = self.tool_bar.addAction(
            qta.icon("fa.chain", color="#ffffff"),
            self.mloc.handle_nxm + " [Experimental]",
        )
        self.nxmhandler_button.setCheckable(True)
        if not self.app.provider.direct_downloads_possible():
            self.tool_bar.widgetForAction(self.nxmhandler_button).setObjectName(
                "accent_button"
            )
        self.nxmhandler_button.triggered.connect(toggle_nxm)

        hlayout.addStretch()

        num_label = QLabel(self.mloc.translations + ":")
        num_label.setObjectName("relevant_label")
        hlayout.addWidget(num_label)

        self.translations_num_label = QLCDNumber()
        self.translations_num_label.setDigitCount(4)
        hlayout.addWidget(self.translations_num_label)

        self.translations_widget = QTreeWidget()
        self.translations_widget.setAlternatingRowColors(True)
        self.translations_widget.header().setSortIndicatorClearable(True)
        self.translations_widget.setSortingEnabled(True)
        self.translations_widget.setUniformRowHeights(True)
        self.translations_widget.sortByColumn(2, Qt.SortOrder.AscendingOrder)

        del_shortcut = QShortcut(QKeySequence("Del"), self.translations_widget)
        del_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        del_shortcut.activated.connect(self.delete_selected)

        def on_sort_change(section: int, order: Qt.SortOrder):
            if section == -1:
                # "Hack" to restore original order by repopulating
                self.load_translations()

        self.translations_widget.header().sortIndicatorChanged.connect(on_sort_change)
        vlayout.addWidget(self.translations_widget)

        self.translations_widget.setHeaderLabels(
            [
                self.mloc.translation_name,
                self.loc.main.version,
                self.loc.main.source,
                self.loc.main.date,
                self.loc.main.size,
            ]
        )

        self.translations_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.translations_widget.header().setStretchLastSection(False)
        self.translations_widget.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )

        def on_context_menu(point: QPoint):
            if not self.translations_widget.selectedItems():
                return

            # Get item at mouse position
            selected_translation: Translation = None
            selected_plugin_name: str = None
            mouse_pos = self.translations_widget.mapFromGlobal(QCursor.pos())
            mouse_pos.setY(mouse_pos.y() - self.translations_widget.header().height())
            current_item = self.translations_widget.itemAt(mouse_pos)

            if current_item is None:
                return

            if parent := current_item.parent():
                matching = [
                    _translation
                    for _translation in self.app.database.user_translations
                    if _translation.tree_item == parent
                ]
                if matching:
                    selected_translation = matching[0]
                    selected_plugin_name = current_item.text(0)
            else:
                matching = [
                    _translation
                    for _translation in self.app.database.user_translations
                    if _translation.tree_item == current_item
                ]
                if matching:
                    selected_translation = matching[0]

            if not selected_translation:
                return

            def show_strings():
                if selected_plugin_name:
                    strings = selected_translation.strings[selected_plugin_name]

                    dialog = StringListDialog(
                        self.app,
                        f"{selected_translation.name} > {selected_plugin_name}",
                        strings,
                        show_translation=True,
                    )
                    dialog.show()
                else:
                    dialog = StringListDialog(
                        self.app,
                        selected_translation.name,
                        selected_translation.strings,
                        show_translation=True,
                    )
                    dialog.show()

            def edit_translation():
                self.app.translation_editor.open_translation(selected_translation)
                self.app.tab_widget.setCurrentWidget(self.app.translation_editor)

            def rename_translation():
                dialog = QInputDialog(self.app.root)
                dialog.setWindowTitle(self.mloc.rename_translation)
                dialog.setLabelText(self.mloc.enter_translation_name)
                dialog.setInputMode(QInputDialog.InputMode.TextInput)
                dialog.setTextValue(selected_translation.name)
                dialog.setOkButtonText(self.loc.main.ok)
                dialog.setCancelButtonText(self.loc.main.cancel)
                dialog.setMinimumWidth(800)
                size = dialog.size()
                size.setWidth(800)
                dialog.resize(size)
                apply_dark_title_bar(dialog)

                if dialog.exec() == dialog.DialogCode.Accepted:
                    old_name = selected_translation.name
                    new_name = dialog.textValue()
                    new_path = (
                        self.app.database.userdb_path
                        / self.app.user_config["language"]
                        / new_name
                    )
                    os.rename(selected_translation.path, new_path)
                    selected_translation.name = new_name
                    selected_translation.path = new_path
                    selected_translation.tree_item.setText(0, new_name)
                    self.app.database.save_database()
                    self.app.log.info(
                        f"Renamed translation {old_name!r} to {new_name!r}."
                    )

            def export_translation():
                items = self.translations_widget.selectedItems()
                selected_translations = [
                    _translation
                    for _translation in self.app.database.user_translations
                    if _translation.tree_item in items
                ]
                if not selected_translations:
                    return

                file_dialog = QFileDialog(self.app.root)
                file_dialog.setWindowTitle(self.mloc.export_translation)
                file_dialog.setFileMode(QFileDialog.FileMode.Directory)
                apply_dark_title_bar(file_dialog)

                if file_dialog.exec():
                    folder = file_dialog.selectedFiles()[0]
                    folder = os.path.normpath(folder)
                    folder = Path(folder)

                    for translation in selected_translations:
                        translation.export_translation(folder)

                    messagebox = QMessageBox(self.app.root)
                    messagebox.setWindowTitle(self.loc.main.success)
                    messagebox.setText(self.mloc.export_complete)
                    apply_dark_title_bar(messagebox)
                    messagebox.exec()

            def apply_translation():
                messagebox = QMessageBox()
                apply_dark_title_bar(messagebox)
                messagebox.setIcon(messagebox.Icon.Warning)
                messagebox.setWindowTitle(self.loc.main.warning)
                messagebox.setText(
                    "This feature is highly experimental and there is a high chance that the plugin won't work at all. Use at your own risk!"
                )
                messagebox.setStandardButtons(
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.Cancel
                )
                messagebox.button(QMessageBox.StandardButton.Cancel).setText(
                    self.loc.main.cancel
                )
                messagebox.button(QMessageBox.StandardButton.Yes).setText(
                    self.loc.main._continue
                )
                choice = messagebox.exec()

                if choice != QMessageBox.StandardButton.Yes:
                    return

                # Find original plugin
                original_plugin: Plugin | None = None
                for mod in self.app.mainpage_widget.mods:
                    for plugin in mod.plugins:
                        if (
                            plugin.name.lower() == selected_plugin_name.lower()
                            and plugin.tree_item.checkState(0)
                            == Qt.CheckState.Checked
                            and plugin.status != plugin.Status.IsTranslated
                        ):
                            original_plugin = plugin

                if not original_plugin:
                    raise Exception("Original plugin not found!")

                file_dialog = QFileDialog(self.app.root)
                file_dialog.setWindowTitle("Apply Translation to Plugin...")
                file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
                file_dialog.setNameFilter(
                    f"Plugin File (*{original_plugin.path.suffix})"
                )
                file_dialog.selectFile(original_plugin.name)
                apply_dark_title_bar(file_dialog)

                if file_dialog.exec():
                    file = file_dialog.selectedFiles()[0]
                    file = os.path.normpath(file)
                    file = Path(file)

                    plugin = plugin_interface.Plugin(original_plugin.path)
                    plugin.replace_strings(
                        selected_translation.strings[selected_plugin_name]
                    )

                    with file.open("wb") as stream:
                        stream.write(plugin.dump())

                    messagebox = QMessageBox(self.app.root)
                    messagebox.setWindowTitle(self.loc.main.success)
                    messagebox.setText(self.mloc.export_complete)
                    apply_dark_title_bar(messagebox)
                    messagebox.exec()

            def open_modpage():
                if selected_translation.mod_id:
                    url = self.app.provider.get_modpage_link(
                        selected_translation.mod_id, source=selected_translation.source
                    )
                    os.startfile(url)

            def open_in_explorer():
                if selected_plugin_name:
                    plugin_path = selected_translation.path / (
                        selected_plugin_name + ".ats"
                    )
                    if plugin_path.is_file():
                        os.system(f'explorer.exe /select,"{plugin_path}"')
                else:
                    if selected_translation.path.is_dir():
                        os.system(f'explorer.exe "{selected_translation.path}"')

            def ignore_update():
                selected_translation.status = Translation.Status.UpdateIgnored
                self.update_translations()

            menu = QMenu()

            expand_all_action = menu.addAction(self.loc.main.expand_all)
            expand_all_action.setIcon(
                qta.icon("mdi6.arrow-expand-vertical", color="#ffffff")
            )
            expand_all_action.triggered.connect(self.translations_widget.expandAll)

            collapse_all_action = menu.addAction(self.loc.main.collapse_all)
            collapse_all_action.setIcon(
                qta.icon("mdi6.arrow-collapse-vertical", color="#ffffff")
            )
            collapse_all_action.triggered.connect(self.translations_widget.collapseAll)

            if selected_translation.status == Translation.Status.UpdateAvailable:
                menu.addSeparator()

                ignore_update_action = menu.addAction(
                    qta.icon("mdi6.cloud-alert", color="#ffffff"),
                    self.loc.updater.ignore_update,
                )
                ignore_update_action.triggered.connect(ignore_update)

            menu.addSeparator()

            show_strings_action = menu.addAction(self.loc.main.show_strings)
            show_strings_action.setIcon(
                qta.icon("mdi6.book-open-outline", color="#ffffff")
            )
            show_strings_action.triggered.connect(show_strings)

            if not selected_plugin_name:
                edit_translation_action = menu.addAction(self.mloc.edit_translation)
                edit_translation_action.setIcon(
                    qta.icon("mdi6.book-edit", color="#ffffff")
                )
                edit_translation_action.triggered.connect(edit_translation)

                rename_translation_action = menu.addAction(self.mloc.rename_translation)
                rename_translation_action.setIcon(
                    qta.icon("mdi6.rename", color="#ffffff")
                )
                rename_translation_action.triggered.connect(rename_translation)

                export_translation_action = menu.addAction(self.mloc.export_translation)
                export_translation_action.setIcon(
                    qta.icon("fa5s.share", color="#ffffff")
                )
                export_translation_action.triggered.connect(export_translation)
            else:
                apply_translation_action = menu.addAction(
                    "Apply Translation to Plugin [HIGHLY EXPERIMENTAL]"
                )
                apply_translation_action.setIcon(
                    qta.icon("fa5s.file-signature", color="#ffffff")
                )
                apply_translation_action.triggered.connect(apply_translation)

            menu.addSeparator()

            if selected_translation.source == Source.NexusMods:
                open_modpage_action = menu.addAction(self.loc.main.open_on_nexusmods)
                open_modpage_action.setIcon(
                    QIcon(str(self.app.res_path / "icons" / "nexus_mods.svg"))
                )
                open_modpage_action.triggered.connect(open_modpage)
            elif selected_translation.source == Source.Confrerie:
                open_modpage_action = menu.addAction(self.loc.main.open_on_confrerie)
                open_modpage_action.setIcon(
                    QIcon(str(self.app.res_path / "icons" / "cdt.svg"))
                )
                open_modpage_action.triggered.connect(open_modpage)

            open_in_explorer_action = menu.addAction(self.loc.main.open_in_explorer)
            open_in_explorer_action.setIcon(qta.icon("fa5s.folder", color="#ffffff"))
            open_in_explorer_action.triggered.connect(open_in_explorer)

            menu.addSeparator()

            delete_action = menu.addAction(self.loc.main.delete_selected)
            delete_action.setIcon(qta.icon("mdi6.trash-can", color="#ffffff"))
            delete_action.triggered.connect(self.delete_selected)
            delete_action.setShortcut(QKeySequence("Del"))

            menu.exec(self.translations_widget.mapToGlobal(point), at=expand_all_action)

        self.translations_widget.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.translations_widget.customContextMenuRequested.connect(on_context_menu)

    @staticmethod
    def is_valid_translation_file(path: Path | str):
        path = Path(path)

        SUPPORTED_EXTS = [".7z", ".rar", ".zip", ".esp", ".esm", ".esl"]

        return path.is_file() and path.suffix.lower() in SUPPORTED_EXTS

    def dragEnterEvent(self, event: QDragEnterEvent):
        if (
            all(
                self.is_valid_translation_file(url.toLocalFile())
                for url in event.mimeData().urls()
            )
            and event.mimeData().hasUrls()
        ):
            event.acceptProposedAction()
            return

        super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent):
        if (
            all(
                self.is_valid_translation_file(url.toLocalFile())
                for url in event.mimeData().urls()
            )
            and event.mimeData().hasUrls()
        ):
            event.acceptProposedAction()
            return

        super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()

        if (
            all(self.is_valid_translation_file(url.toLocalFile()) for url in urls)
            and urls
        ):
            files = [Path(file.toLocalFile()) for file in urls]
            if files:
                self.import_local_translation(files)
            event.acceptProposedAction()
            return

        super().dropEvent(event)

    def search_database(self):
        """
        Opens dialog for searching the entire translation database.
        """

        dialog = QDialog(self.app.root)
        dialog.setWindowTitle(self.mloc.search_database)
        dialog.setModal(True)
        dialog.setMinimumWidth(700)
        apply_dark_title_bar(dialog)

        flayout = QFormLayout()
        dialog.setLayout(flayout)

        type_box = QCheckBox(self.loc.main.type)
        type_entry = QLineEdit()
        type_entry.setDisabled(True)
        type_box.stateChanged.connect(
            lambda state: type_entry.setEnabled(
                state == Qt.CheckState.Checked.value
            )
        )
        type_box.clicked.connect(type_entry.setFocus)
        flayout.addRow(type_box, type_entry)

        formid_box = QCheckBox(self.loc.main.form_id)
        formid_entry = QLineEdit()
        formid_entry.setDisabled(True)
        formid_box.stateChanged.connect(
            lambda state: formid_entry.setEnabled(
                state == Qt.CheckState.Checked.value
            )
        )
        formid_box.clicked.connect(formid_entry.setFocus)
        flayout.addRow(formid_box, formid_entry)

        edid_box = QCheckBox(self.loc.main.editor_id)
        edid_entry = QLineEdit()
        edid_entry.setDisabled(True)
        edid_box.stateChanged.connect(
            lambda state: edid_entry.setEnabled(
                state == Qt.CheckState.Checked.value
            )
        )
        edid_box.clicked.connect(edid_entry.setFocus)
        flayout.addRow(edid_box, edid_entry)

        original_box = QRadioButton(self.loc.main.original)
        original_entry = QLineEdit()
        original_entry.setDisabled(True)
        original_box.toggled.connect(
            lambda: original_entry.setEnabled(original_box.isChecked())
        )
        original_box.clicked.connect(original_entry.setFocus)
        flayout.addRow(original_box, original_entry)

        string_box = QRadioButton(self.loc.main.string)
        string_entry = QLineEdit()
        string_entry.setDisabled(True)
        string_box.toggled.connect(
            lambda: string_entry.setEnabled(string_box.isChecked())
        )
        string_box.clicked.connect(string_entry.setFocus)
        flayout.addRow(string_box, string_entry)

        hlayout = QHBoxLayout()
        flayout.addRow(hlayout)

        cancel_button = ShortcutButton(self.loc.main.cancel)
        cancel_button.setShortcut(QKeySequence("Esc"))
        cancel_button.clicked.connect(dialog.reject)
        hlayout.addWidget(cancel_button)

        hlayout.addStretch()

        search_button = ShortcutButton(self.loc.main.search[:-3])
        search_button.setObjectName("accent_button")
        search_button.setShortcut(QKeySequence("Return"))
        search_button.clicked.connect(dialog.accept)
        hlayout.addWidget(search_button)

        if dialog.exec() == dialog.DialogCode.Accepted:
            filter: dict[str, str] = {}

            if type_box.isChecked():
                filter["type"] = type_entry.text()

            if formid_box.isChecked():
                filter["form_id"] = formid_entry.text()

            if edid_box.isChecked():
                filter["editor_id"] = edid_entry.text()

            if original_box.isChecked() and original_entry.text():
                filter["original"] = original_entry.text()
            elif string_box.isChecked() and string_box.text():
                filter["string"] = string_entry.text()

            matching = self.app.database.search_database(filter)

            if len(matching):
                dialog = StringListDialog(
                    self.app,
                    self.loc.main.scan_result,
                    matching,
                    show_translation=True,
                )
                dialog.show()
            else:
                dialog = ErrorDialog(
                    self.app.root,
                    self.app,
                    title=self.loc.main.no_strings_found,
                    text=self.loc.main.no_strings_found_text,
                    details=str(filter),
                    yesno=False,
                )
                dialog.exec()

    def delete_selected(self):
        items = self.translations_widget.selectedItems()
        matching = [
            _translation
            for _translation in self.app.database.user_translations
            if _translation.tree_item in items
        ]
        if matching:
            message_box = QMessageBox(self.app.root)
            message_box.setWindowTitle(self.loc.main.delete)
            message_box.setText(self.loc.main.delete_text)
            message_box.setStandardButtons(
                QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(QMessageBox.StandardButton.Yes)
            message_box.button(QMessageBox.StandardButton.No).setText(
                self.loc.main.no
            )
            message_box.button(QMessageBox.StandardButton.Yes).setText(
                self.loc.main.yes
            )
            apply_dark_title_bar(message_box)
            if message_box.exec() != QMessageBox.StandardButton.Yes:
                return

            self.app.log.info("Deleting selected translations...")
            for translation in matching:
                self.app.translation_editor.close_translation(translation, silent=True)
                self.app.database.delete_translation(translation)
            self.app.log.info("Translations deleted. Updating database...")

            self.load_translations()
            self.app.mainpage_widget.update_modlist()

            self.app.log.info("Database updated.")

    def check_for_updates(self):
        """
        Checks downloaded translations for updates.
        """

        self.app.log.info("Checking installed translations for updates...")

        def process(ldialog: LoadingDialog):
            translations = [
                translation
                for translation in self.app.database.user_translations
                if translation.mod_id
                and translation.status != translation.Status.UpdateIgnored
                and translation.status != translation.Status.UpdateAvailable
                and translation.source != Source.Local
            ]

            for t, translation in enumerate(translations):
                ldialog.updateProgress(
                    text1=f"{self.mloc.checking_for_updates} ({t}/{len(translations)})",
                    value1=t,
                    max1=len(translations),
                    show2=True,
                    text2=translation.name,
                )

                if self.app.provider.is_update_available(
                    translation.mod_id,
                    translation.file_id,
                    translation.timestamp,
                    translation.source,
                ):
                    translation.status = translation.Status.UpdateAvailable

        loadingdialog = LoadingDialog(self.app.root, self.app, process)
        loadingdialog.exec()

        self.update_translations()

        self.app.log.info("Update check complete.")

        available_updates = len(
            [
                translation
                for translation in self.app.database.user_translations
                if translation.status == translation.Status.UpdateAvailable
            ]
        )

        messagebox = QMessageBox(self.app.root)
        messagebox.setWindowTitle(self.mloc.update_check_complete)
        messagebox.setText(
            self.mloc.updates_available.replace("[NUMBER]", str(available_updates))
        )
        apply_dark_title_bar(messagebox)
        messagebox.exec()

    def download_updates(self):
        """
        Creates download list for available translation updates.
        """

        self.app.log.info("Getting downloads for translation updates...")

        downloads: dict[str, list[TranslationDownload]] = {}

        def process(ldialog: LoadingDialog):
            ldialog.updateProgress(text1=self.loc.main.getting_downloads)

            translations = [
                translation
                for translation in self.app.database.user_translations
                if translation.status == translation.Status.UpdateAvailable
            ]

            for translation in translations:
                new_file_id = self.app.provider.get_updated_file_id(
                    translation.mod_id, translation.file_id
                )

                matching_mods = list(
                    filter(
                        lambda mod: (
                            mod.mod_id == translation.original_mod_id
                            and any(
                                plugin_name
                                in [plugin.name.lower() for plugin in mod.plugins]
                                for plugin_name in translation.strings
                            )
                        ),
                        self.app.mainpage_widget.mods,
                    )
                )

                if not matching_mods:
                    self.app.log.warning(
                        f"Failed to update translation {translation.name!r}: Original Mod not installed!"
                    )
                    continue

                original_mod = matching_mods[0]
                original_plugin = original_mod.plugins[0]

                if new_file_id is None and translation.source == Source.NexusMods:
                    translation.status = translation.Status.Ok
                    continue

                download = TranslationDownload(
                    name=translation.name,
                    mod_id=translation.mod_id,
                    original_mod=original_mod,
                    original_plugin=original_plugin,
                    source=translation.source,
                    available_downloads=[
                        FileDownload(
                            name=translation.name,
                            source=translation.source,
                            mod_id=translation.mod_id,
                            file_id=new_file_id,
                            original_mod=original_mod,
                            file_name=self.app.provider.get_details(
                                translation.mod_id, new_file_id, translation.source
                            )["filename"],
                        )
                    ],
                )
                downloads[translation.name] = [download]

        loadingdialog = LoadingDialog(self.app.root, self.app, process)
        loadingdialog.exec()

        self.tool_bar.widgetForAction(self.download_updates_button).setObjectName("")
        self.tool_bar.setStyleSheet(self.app.styleSheet())

        if len(downloads):
            DownloadListDialog(self.app, downloads, updates=True)

    def update_translations(self, *args):
        """
        Updates translations in case of search or similar.
        """

        cur_search = self.app.mainpage_widget.search_bar.text()
        case_sensitive = self.app.mainpage_widget.search_bar.cs_toggle.isChecked()

        for translation in self.app.database.user_translations:
            if not translation.tree_item:
                continue

            if case_sensitive:
                translation_visible = cur_search in translation.name
            else:
                translation_visible = cur_search.lower() in translation.name.lower()

            for cindex in range(translation.tree_item.childCount()):
                plugin_item = translation.tree_item.child(cindex)

                if case_sensitive:
                    plugin_visible = cur_search in plugin_item.text(0)
                else:
                    plugin_visible = cur_search.lower() in plugin_item.text(0).lower()

                if plugin_visible:
                    translation_visible = True

                plugin_item.setHidden(not plugin_visible)

            if translation.status == translation.Status.UpdateAvailable:
                translation.tree_item.setForeground(1, Qt.GlobalColor.yellow)
            else:
                translation.tree_item.setForeground(1, Qt.GlobalColor.white)

            translation.tree_item.setHidden(not translation_visible)

        if any(
            translation.status == translation.Status.UpdateAvailable
            for translation in self.app.database.user_translations
        ):
            self.download_updates_button.setDisabled(False)
            self.tool_bar.widgetForAction(self.download_updates_button).setObjectName(
                "accent_button"
            )
            self.tool_bar.setStyleSheet(self.app.styleSheet())
        else:
            self.download_updates_button.setDisabled(True)
            self.tool_bar.widgetForAction(self.download_updates_button).setObjectName(
                ""
            )
            self.tool_bar.setStyleSheet(self.app.styleSheet())

        if self.translations_widget.selectedItems():
            self.translations_widget.scrollToItem(
                self.translations_widget.selectedItems()[0],
                QTreeWidget.ScrollHint.PositionAtCenter,
            )

    def load_translations(self):
        """
        Loads translations from database and displays translations on screen.
        """

        self.translations_widget.clear()

        for translation in self.app.database.user_translations:
            translation_size = get_folder_size(translation.path)
            translation_item = QTreeWidgetItem(
                [
                    translation.name,
                    translation.version,
                    translation.source.name,
                    (
                        fmt_timestamp(translation.timestamp, "%d.%m.%Y %H:%M")
                        if translation.timestamp is not None
                        else ""
                    ),
                    scale_value(translation_size),
                ]
            )

            if translation.timestamp is not None:
                translation_item.setToolTip(
                    3, fmt_timestamp(translation.timestamp, "%d.%m.%Y %H:%M:%S")
                )
            translation_item.setToolTip(4, f"{translation_size} Bytes")

            for plugin_name in translation.strings:
                plugin_item = QTreeWidgetItem(
                    [
                        plugin_name,
                        "",
                        "",
                        "",
                        "",
                    ]
                )
                translation_item.addChild(plugin_item)

            translation.tree_item = translation_item
            self.translations_widget.addTopLevelItem(translation_item)

        self.translations_num_label.display(len(self.app.database.user_translations))

        if hasattr(self.app, "mainpage_widget"):
            self.update_translations()

    def import_local_translation(self, files: list[Path] | None = None):
        """
        Shows File Dialog for importing a local translation.
        """

        modlist = self.app.mainpage_widget.mods

        installed_mods = {
            plugin.name.lower(): plugin
            for mod in modlist
            for plugin in mod.plugins
            if plugin.status != plugin.Status.TranslationInstalled
            and plugin.status != plugin.Status.TranslationIncomplete
        }

        if not files:
            fdialog = QFileDialog()
            fdialog.setFileMode(fdialog.FileMode.ExistingFiles)
            fdialog.setNameFilters(
                [
                    "Mod Archive (*.7z *.rar *.zip)",
                    "Bethesda Plugin (*.esp *.esm *.esl)",
                ]
            )
            fdialog.setWindowTitle(self.mloc.import_local)

            if fdialog.exec() == fdialog.DialogCode.Rejected:
                return

            files = [Path(file) for file in fdialog.selectedFiles()]

        if files:
            for file in files:
                strings: dict[str, list[String]] = {}

                if file.suffix.lower() in [".7z", ".rar", ".zip"]:
                    self.app.log.info(f"Importing translation from archive '{file}'...")

                    __temp = []

                    def process(ldialog: LoadingDialog):
                        __temp.append(
                            import_from_archive(
                                file,
                                modlist,
                                self.app.get_tmp_dir(),
                                self.app.cacher,
                                ldialog,
                            )
                        )

                    loadingdialog = LoadingDialog(self.app.root, self.app, process)
                    loadingdialog.exec()

                    strings = __temp[0]

                elif file.suffix.lower() in [".esp", ".esm", ".esl"]:
                    self.app.log.info(f"Importing translation from '{file}'...")

                    plugin = installed_mods.get(file.name.lower())

                    if plugin is None:
                        self.app.log.error(
                            f"No original plugin for {file.name!r} found!"
                        )
                        continue

                    plugin_strings = merge_plugin_strings(
                        file, plugin.path, self.app.cacher
                    )
                    strings[file.name.lower()] = plugin_strings

                else:
                    continue

                if len(strings):
                    translation = Translation(
                        name=file.stem,
                        mod_id=0,
                        file_id=0,
                        version="",
                        original_mod_id=0,
                        original_file_id=0,
                        original_version="",
                        path=self.app.database.userdb_path
                        / self.app.database.language
                        / file.stem,
                        source=Source.Local,
                        timestamp=int(time.time()),
                    )
                    translation.strings = strings
                    translation.save_translation()
                    self.app.database.add_translation(translation)

                    original_mod: Mod = None

                    for mod in self.app.mainpage_widget.mods:
                        if any(
                            list(strings.keys())[0].lower() == plugin.name.lower()
                            for plugin in mod.plugins
                        ):
                            translation.original_mod_id = mod.mod_id
                            translation.original_file_id = mod.file_id
                            translation.original_version = mod.version
                            original_mod = mod
                            break

                    if original_mod and file.suffix.lower() in [".7z", ".rar", ".zip"]:

                        def process(ldialog: LoadingDialog):
                            import_non_plugin_files(
                                file,
                                original_mod,
                                translation,
                                self.app.get_tmp_dir(),
                                self.app.user_config,
                                ldialog,
                            )

                        loadingdialog = LoadingDialog(self.app.root, self.app, process)
                        loadingdialog.exec()
                    elif file.suffix.lower() in [".7z", ".rar", ".zip"]:
                        self.app.log.info(
                            f"Failed to import non-Plugin files! No original mod found!"
                        )

                    self.app.log.info(f"Translation {translation.name!r} imported.")
                else:
                    self.app.log.info(
                        "Translation not imported. Translation does not contain any strings!"
                    )

            self.load_translations()
            self.app.mainpage_widget.update_modlist()

            messagebox = QMessageBox(self.app.root)
            messagebox.setWindowTitle(self.loc.main.success)
            messagebox.setText(self.mloc.translations_imported)
            apply_dark_title_bar(messagebox)
            messagebox.exec()
