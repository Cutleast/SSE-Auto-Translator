"""
This file is part of SEE Auto Translator
and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os
from pathlib import Path

import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import utilities as utils
from main import MainApp
from widgets import DownloadListDialog, LoadingDialog, StringListDialog

from .translation import Translation


class TranslationsWidget(qtw.QWidget):
    """
    Tab for Translations Database.
    """

    def __init__(self, app: MainApp):
        super().__init__()

        self.app = app
        self.loc = app.loc
        self.mloc = app.loc.database

        vlayout = qtw.QVBoxLayout()
        self.setLayout(vlayout)

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.tool_bar = qtw.QToolBar()
        hlayout.addWidget(self.tool_bar)

        show_vanilla_strings_action = self.tool_bar.addAction(
            qta.icon("mdi6.book-open-outline", color="#ffffff"),
            self.mloc.show_vanilla_strings,
        )

        def show_vanilla_strings():
            vanilla_strings = list(
                set(  # Remove duplicates
                    [
                        string
                        for plugin_strings in self.app.database.vanilla_translation.strings.values()
                        for string in plugin_strings
                    ]
                )
            )

            dialog = StringListDialog(
                self.app,
                "Base Game + AE CC Content",
                vanilla_strings,
                show_translation=True,
            )
            dialog.show()

        show_vanilla_strings_action.triggered.connect(show_vanilla_strings)

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
        if not self.app.api.premium:
            self.tool_bar.widgetForAction(self.nxmhandler_button).setObjectName(
                "accent_button"
            )
        self.nxmhandler_button.triggered.connect(toggle_nxm)

        hlayout.addStretch()

        num_label = qtw.QLabel(self.mloc.translations + ":")
        num_label.setObjectName("relevant_label")
        hlayout.addWidget(num_label)

        self.translations_num_label = qtw.QLCDNumber()
        self.translations_num_label.setDigitCount(4)
        hlayout.addWidget(self.translations_num_label)

        self.translations_widget = qtw.QTreeWidget()
        self.translations_widget.setAlternatingRowColors(True)
        self.translations_widget.header().setSortIndicatorClearable(True)
        self.translations_widget.setSortingEnabled(True)
        self.translations_widget.sortByColumn(2, qtc.Qt.SortOrder.AscendingOrder)

        del_shortcut = qtg.QShortcut(qtg.QKeySequence("Del"), self.translations_widget)
        del_shortcut.setContext(qtc.Qt.ShortcutContext.WidgetWithChildrenShortcut)
        del_shortcut.activated.connect(self.delete_selected)

        def on_sort_change(section: int, order: qtc.Qt.SortOrder):
            if section == -1:
                # "Hack" to restore original order by repopulating
                self.load_translations()

        self.translations_widget.header().sortIndicatorChanged.connect(on_sort_change)
        vlayout.addWidget(self.translations_widget)

        self.translations_widget.setHeaderLabels(
            [
                self.mloc.translation_name,
                self.loc.main.version,
            ]
        )

        self.translations_widget.setSelectionMode(
            qtw.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.translations_widget.header().setStretchLastSection(False)
        self.translations_widget.header().setSectionResizeMode(
            0, qtw.QHeaderView.ResizeMode.Stretch
        )

        def on_context_menu(point: qtc.QPoint):
            if not self.translations_widget.selectedItems():
                return

            # Get item at mouse position
            selected_translation: Translation = None
            selected_plugin_name: str = None
            mouse_pos = self.translations_widget.mapFromGlobal(qtg.QCursor.pos())
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
                        True,
                    )
                    dialog.show()
                else:
                    strings = [
                        string
                        for plugin_strings in selected_translation.strings.values()
                        for string in plugin_strings
                    ]

                    dialog = StringListDialog(
                        self.app, selected_translation.name, strings, True
                    )
                    dialog.show()

            def edit_translation():
                self.app.translation_editor.open_translation(selected_translation)
                self.app.tab_widget.setCurrentWidget(self.app.translation_editor)

            def rename_translation():
                dialog = qtw.QInputDialog(self.app.root)
                dialog.setWindowTitle(self.mloc.rename_translation)
                dialog.setLabelText(self.mloc.enter_translation_name)
                dialog.setInputMode(qtw.QInputDialog.InputMode.TextInput)
                dialog.setTextValue(selected_translation.name)
                dialog.setOkButtonText(self.loc.main.ok)
                dialog.setCancelButtonText(self.loc.main.cancel)
                dialog.setMinimumWidth(800)
                size = dialog.size()
                size.setWidth(800)
                dialog.resize(size)
                utils.apply_dark_title_bar(dialog)

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
                file_dialog = qtw.QFileDialog(self.app.root)
                file_dialog.setWindowTitle(self.mloc.export_translation)
                file_dialog.setFileMode(qtw.QFileDialog.FileMode.Directory)
                utils.apply_dark_title_bar(file_dialog)

                if file_dialog.exec():
                    folder = file_dialog.selectedFiles()[0]
                    folder = os.path.normpath(folder)
                    folder = Path(folder)

                    selected_translation.export_translation(folder)

                    messagebox = qtw.QMessageBox(self.app.root)
                    messagebox.setWindowTitle(self.loc.main.success)
                    messagebox.setText(self.mloc.export_complete)
                    utils.apply_dark_title_bar(messagebox)
                    messagebox.exec()

            def open_modpage():
                if selected_translation.mod_id:
                    url = utils.create_nexus_mods_url(
                        "skyrimspecialedition", selected_translation.mod_id
                    )
                    os.startfile(url)

            def open_in_explorer():
                if selected_plugin_name:
                    plugin_path = selected_translation.path / (
                        selected_plugin_name + ".json"
                    )
                    if plugin_path.is_file():
                        os.system(f'explorer.exe /select,"{plugin_path}"')
                else:
                    if selected_translation.path.is_dir():
                        os.system(f'explorer.exe "{selected_translation.path}"')

            def ignore_update():
                selected_translation.status = Translation.Status.UpdateIgnored
                self.update_translations()

            menu = qtw.QMenu()

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

            menu.addSeparator()

            open_modpage_action = menu.addAction(self.loc.main.open_on_nexusmods)
            open_modpage_action.setIcon(
                qtg.QIcon(str(self.app.data_path / "icons" / "nexus_mods.svg"))
            )
            open_modpage_action.triggered.connect(open_modpage)
            open_modpage_action.setDisabled(selected_translation.mod_id == 0)

            open_in_explorer_action = menu.addAction(self.loc.main.open_in_explorer)
            open_in_explorer_action.setIcon(qta.icon("fa5s.folder", color="#ffffff"))
            open_in_explorer_action.triggered.connect(open_in_explorer)

            menu.addSeparator()

            delete_action = menu.addAction(self.loc.main.delete_selected)
            delete_action.setIcon(qta.icon("mdi6.trash-can", color="#ffffff"))
            delete_action.triggered.connect(self.delete_selected)
            delete_action.setShortcut(qtg.QKeySequence("Del"))

            menu.exec(self.translations_widget.mapToGlobal(point), at=expand_all_action)

        self.translations_widget.setContextMenuPolicy(
            qtc.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.translations_widget.customContextMenuRequested.connect(on_context_menu)

    def delete_selected(self):
        items = self.translations_widget.selectedItems()
        matching = [
            _translation
            for _translation in self.app.database.user_translations
            if _translation.tree_item in items
        ]
        if matching:
            message_box = qtw.QMessageBox(self.app.root)
            message_box.setWindowTitle(self.loc.main.delete)
            message_box.setText(self.loc.main.delete_text)
            message_box.setStandardButtons(
                qtw.QMessageBox.StandardButton.No
                | qtw.QMessageBox.StandardButton.Yes
            )
            message_box.setDefaultButton(qtw.QMessageBox.StandardButton.Yes)
            message_box.button(qtw.QMessageBox.StandardButton.No).setText(
                self.loc.main.no
            )
            message_box.button(qtw.QMessageBox.StandardButton.Yes).setText(
                self.loc.main.yes
            )
            utils.apply_dark_title_bar(message_box)
            if message_box.exec() != qtw.QMessageBox.StandardButton.Yes:
                return

            self.app.log.info("Deleting selected translations...")
            for translation in matching:
                self.app.translation_editor.close_translation(
                    translation, silent=True
                )
                self.app.database.delete_translation(translation)
            self.app.log.info("Translations deleted. Updating database...")

            self.app.database.save_database()
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
                and translation.file_id
                and translation.status != translation.Status.UpdateIgnored
                and translation.status != translation.Status.UpdateAvailable
            ]

            for t, translation in enumerate(translations):
                ldialog.updateProgress(
                    text1=f"{self.mloc.checking_for_updates} ({t}/{len(translations)})",
                    value1=t,
                    max1=len(translations),
                    show2=True,
                    text2=translation.name,
                )

                updates = self.app.api.get_mod_updates(
                    "skyrimspecialedition", translation.mod_id
                )
                if translation.file_id in updates.keys():
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

        messagebox = qtw.QMessageBox(self.app.root)
        messagebox.setWindowTitle(self.mloc.update_check_complete)
        messagebox.setText(
            self.mloc.updates_available.replace("[NUMBER]", str(available_updates))
        )
        utils.apply_dark_title_bar(messagebox)
        messagebox.exec()

    def download_updates(self):
        """
        Creates download list for available translation updates.
        """

        self.app.log.info("Getting downloads for translation updates...")

        downloads: list[utils.Download] = []

        def process(ldialog: LoadingDialog):
            ldialog.updateProgress(text1=self.loc.main.getting_downloads)

            translations = [
                translation
                for translation in self.app.database.user_translations
                if translation.status == translation.Status.UpdateAvailable
            ]

            for translation in translations:
                updates = self.app.api.get_mod_updates(
                    "skyrimspecialedition", translation.mod_id
                )

                old_file_id = translation.file_id
                new_file_id = None

                while old_file_id := updates.get(old_file_id):
                    new_file_id = old_file_id

                if new_file_id is None:
                    translation.status = translation.Status.Ok
                    continue

                self.app.log.debug(
                    f"Available update for {translation.name!r}: {new_file_id}"
                )

                download = utils.Download(
                    translation.name,
                    translation.mod_id,
                    str(translation.file_id),
                    available_translations=[translation.mod_id],
                    available_translation_files={translation.mod_id: [new_file_id]},
                )
                downloads.append(download)

        loadingdialog = LoadingDialog(self.app.root, self.app, process)
        loadingdialog.exec()

        self.tool_bar.widgetForAction(self.download_updates_button).setObjectName("")
        self.tool_bar.setStyleSheet(self.app.styleSheet())

        if len(downloads):
            DownloadListDialog(self.app, downloads, updates=True)

    def update_translations(self):
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
                translation.tree_item.setForeground(1, qtc.Qt.GlobalColor.yellow)
            else:
                translation.tree_item.setForeground(1, qtc.Qt.GlobalColor.white)

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
                qtw.QTreeWidget.ScrollHint.PositionAtCenter,
            )

    def load_translations(self):
        """
        Loads translations from database and displays translations on screen.
        """

        self.translations_widget.clear()

        for translation in self.app.database.user_translations:
            translation_item = qtw.QTreeWidgetItem(
                [
                    translation.name,
                    translation.version,
                ]
            )

            for plugin_name in translation.strings:
                plugin_item = qtw.QTreeWidgetItem(
                    [
                        plugin_name,
                        "",
                    ]
                )
                translation_item.addChild(plugin_item)

            translation.tree_item = translation_item
            self.translations_widget.addTopLevelItem(translation_item)

        self.translations_num_label.display(len(self.app.database.user_translations))

    def import_local_translation(self):
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

        fdialog = qtw.QFileDialog()
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

        selected_files = fdialog.selectedFiles()

        if selected_files:
            for file in selected_files:
                file = Path(file)

                strings: dict[str, list[utils.String]] = {}

                if file.suffix.lower() in [".7z", ".rar", ".zip"]:
                    self.app.log.info(f"Importing translation from archive '{file}'...")

                    __temp = []

                    def process(ldialog: LoadingDialog):
                        __temp.append(utils.import_from_archive(file, modlist, ldialog))

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

                    plugin_strings = utils.merge_plugin_strings(file, plugin.path)
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
                    )
                    translation.strings = strings
                    translation.save_translation()
                    self.app.database.add_translation(translation)

                    for mod in self.app.mainpage_widget.mods:
                        if any(
                            list(strings.keys())[0].lower() == plugin.name.lower()
                            for plugin in mod.plugins
                        ):
                            translation.original_mod_id = mod.mod_id
                            translation.original_file_id = mod.file_id
                            translation.original_version = mod.version

                    self.app.log.info(f"Translation {translation.name!r} imported.")
                else:
                    self.app.log.info(
                        "Translation not imported. Translation does not contain any strings!"
                    )

            self.app.database.save_database()
            self.load_translations()
            self.app.mainpage_widget.update_modlist()

            messagebox = qtw.QMessageBox(self.app.root)
            messagebox.setWindowTitle(self.loc.main.success)
            messagebox.setText(self.mloc.translations_imported)
            utils.apply_dark_title_bar(messagebox)
            messagebox.exec()
