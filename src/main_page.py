"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os

import jstyleson as json
import qtawesome as qta
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import utilities as utils
from database import DatabaseWidget
from main import MainApp
from mod_managers import SUPPORTED_MOD_MANAGERS
from plugin_parser import PluginParser
from processor import Processor
from widgets import LoadingDialog, StringListDialog, IgnoreListDialog


class MainPageWidget(qtw.QWidget):
    """
    Main page of AT, displays modlist
    including MO2 separators.
    """

    mods: list[utils.Mod] = None

    ignore_list: list[str] = None

    def __init__(self, app: MainApp):
        super().__init__()

        self.app = app
        self.loc = app.loc
        self.mloc = app.loc.main_page

        vlayout = qtw.QVBoxLayout()
        self.setLayout(vlayout)

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.title_label = qtw.QLabel(self.mloc.modlist)
        self.title_label.setObjectName("relevant_label")
        hlayout.addWidget(self.title_label)

        hlayout.addStretch()

        num_label = qtw.QLabel(self.mloc.plugins + ":")
        num_label.setObjectName("relevant_label")
        hlayout.addWidget(num_label)

        self.plugins_num_label = qtw.QLCDNumber()
        self.plugins_num_label.setDigitCount(4)
        hlayout.addWidget(self.plugins_num_label)

        hlayout = qtw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.tool_bar = qtw.QToolBar()
        self.tool_bar.setIconSize(qtc.QSize(32, 32))
        self.tool_bar.setFloatable(False)
        hlayout.addWidget(self.tool_bar)

        filter_menu = qtw.QMenu()

        self.filter_none = qtw.QCheckBox(self.mloc.filter_none, filter_menu)
        self.filter_none.setObjectName("menu_checkbox")
        self.filter_none.setChecked(True)
        self.filter_none.stateChanged.connect(lambda _: self.update_modlist())
        widget_action = qtw.QWidgetAction(filter_menu)
        widget_action.setDefaultWidget(self.filter_none)
        filter_menu.addAction(widget_action)

        self.filter_no_strings = qtw.QCheckBox(self.mloc.filter_no_strings, filter_menu)
        self.filter_no_strings.setObjectName("menu_checkbox")
        self.filter_no_strings.setChecked(True)
        self.filter_no_strings.stateChanged.connect(lambda _: self.update_modlist())
        widget_action = qtw.QWidgetAction(filter_menu)
        widget_action.setDefaultWidget(self.filter_no_strings)
        filter_menu.addAction(widget_action)

        self.filter_translation_installed = qtw.QCheckBox(
            self.mloc.filter_translation_installed, filter_menu
        )
        self.filter_translation_installed.setObjectName("menu_checkbox")
        self.filter_translation_installed.setChecked(True)
        self.filter_translation_installed.stateChanged.connect(
            lambda _: self.update_modlist()
        )
        widget_action = qtw.QWidgetAction(filter_menu)
        widget_action.setDefaultWidget(self.filter_translation_installed)
        filter_menu.addAction(widget_action)

        self.filter_translation_available = qtw.QCheckBox(
            self.mloc.filter_translation_available, filter_menu
        )
        self.filter_translation_available.setObjectName("menu_checkbox")
        self.filter_translation_available.setChecked(True)
        self.filter_translation_available.stateChanged.connect(
            lambda _: self.update_modlist()
        )
        widget_action = qtw.QWidgetAction(filter_menu)
        widget_action.setDefaultWidget(self.filter_translation_available)
        filter_menu.addAction(widget_action)

        self.filter_translation_incomplete = qtw.QCheckBox(
            self.mloc.filter_translation_incomplete, filter_menu
        )
        self.filter_translation_incomplete.setObjectName("menu_checkbox")
        self.filter_translation_incomplete.setChecked(True)
        self.filter_translation_incomplete.stateChanged.connect(
            lambda _: self.update_modlist()
        )
        widget_action = qtw.QWidgetAction(filter_menu)
        widget_action.setDefaultWidget(self.filter_translation_incomplete)
        filter_menu.addAction(widget_action)

        self.filter_requires_translation = qtw.QCheckBox(
            self.mloc.filter_requires_translation, filter_menu
        )
        self.filter_requires_translation.setObjectName("menu_checkbox")
        self.filter_requires_translation.setChecked(True)
        self.filter_requires_translation.stateChanged.connect(
            lambda _: self.update_modlist()
        )
        widget_action = qtw.QWidgetAction(filter_menu)
        widget_action.setDefaultWidget(self.filter_requires_translation)
        filter_menu.addAction(widget_action)

        self.filter_no_translation_available = qtw.QCheckBox(
            self.mloc.filter_no_translation_available, filter_menu
        )
        self.filter_no_translation_available.setObjectName("menu_checkbox")
        self.filter_no_translation_available.setChecked(True)
        self.filter_no_translation_available.stateChanged.connect(
            lambda _: self.update_modlist()
        )
        widget_action = qtw.QWidgetAction(filter_menu)
        widget_action.setDefaultWidget(self.filter_no_translation_available)
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

        open_ignore_list_action = self.tool_bar.addAction(
            qta.icon("mdi6.playlist-remove", color="#ffffff"),
            self.mloc.open_ignore_list,
        )
        open_ignore_list_action.triggered.connect(self.open_ignore_list)

        help_action = self.tool_bar.addAction(
            qta.icon("mdi6.help", color="#ffffff"), self.mloc.show_help
        )
        help_action.triggered.connect(self.show_help)

        self.tool_bar.addSeparator()

        scan_modlist_action = self.tool_bar.addAction(
            qtg.QIcon(str(self.app.data_path / "icons" / "detect_lang.svg")),
            self.loc.main.scan_modlist,
        )
        self.tool_bar.widgetForAction(scan_modlist_action).setObjectName(
            "accent_button"
        )
        scan_modlist_action.triggered.connect(
            lambda: (
                Processor.scan_modlist(self.mods, self.app),
                self.tool_bar.widgetForAction(scan_nm_action).setObjectName(
                    "accent_button"
                ),
                self.tool_bar.widgetForAction(scan_modlist_action).setObjectName(""),
                self.tool_bar.setStyleSheet(self.app.styleSheet()),
            )
        )

        scan_nm_action = self.tool_bar.addAction(
            qtg.QIcon(str(self.app.data_path / "icons" / "scan_nm.svg")),
            self.loc.main.scan_nm_translations,
        )
        scan_nm_action.triggered.connect(
            lambda: (
                Processor.scan_nm(self.mods, self.app),
                self.tool_bar.widgetForAction(
                    download_translations_action
                ).setObjectName("accent_button"),
                self.tool_bar.widgetForAction(scan_nm_action).setObjectName(""),
                self.tool_bar.setStyleSheet(self.app.styleSheet()),
            )
        )

        download_translations_action = self.tool_bar.addAction(
            qta.icon("mdi6.download-multiple", color="#ffffff"),
            self.loc.main.download_translations,
        )
        download_translations_action.triggered.connect(
            lambda: (
                Processor.download_and_install_translations(self.mods, self.app),
                self.tool_bar.widgetForAction(build_dict_action).setObjectName(
                    "accent_button"
                ),
                self.tool_bar.widgetForAction(
                    download_translations_action
                ).setObjectName(""),
                self.tool_bar.setStyleSheet(self.app.styleSheet()),
            )
        )

        build_dict_action = self.tool_bar.addAction(
            qta.icon("mdi6.export-variant", color="#ffffff"),
            self.loc.main.build_dictionary,
        )
        build_dict_action.triggered.connect(
            lambda: (
                Processor.build_dsd_dictionary(self.mods, self.app),
                self.tool_bar.widgetForAction(build_dict_action).setObjectName(""),
                self.tool_bar.setStyleSheet(self.app.styleSheet()),
            )
        )

        self.tool_bar.addSeparator()

        deep_scan_action = self.tool_bar.addAction(
            qta.icon("mdi6.line-scan", color="#ffffff"),
            self.loc.main.deep_scan + "\n[Experimental]",
        )
        deep_scan_action.triggered.connect(
            lambda: Processor.run_deep_scan(self.mods, self.app)
        )

        self.search_box = qtw.QLineEdit()
        self.search_box.setClearButtonEnabled(True)
        self.search_box.setPlaceholderText(self.loc.main.search)
        self.search_icon: qtg.QAction = self.search_box.addAction(
            qta.icon("fa.search", color="#ffffff"),
            qtw.QLineEdit.ActionPosition.LeadingPosition,
        )
        self.search_box.textChanged.connect(lambda text: self.update_modlist())
        self.search_box.returnPressed.connect(self.update_modlist)
        hlayout.addWidget(self.search_box)

        splitter = qtw.QSplitter()
        vlayout.addWidget(splitter, stretch=1)

        self.mods_widget = qtw.QTreeWidget()
        self.mods_widget.setAlternatingRowColors(True)
        splitter.addWidget(self.mods_widget)

        self.mods_widget.setHeaderLabels(
            [
                self.loc.main.name,
                self.loc.main.version,
                self.mloc.priority,
            ]
        )
        self.mods_widget.header().setDefaultAlignment(qtc.Qt.AlignmentFlag.AlignCenter)
        self.mods_widget.setSelectionMode(
            qtw.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.mods_widget.header().setSectionResizeMode(
            0, qtw.QHeaderView.ResizeMode.Stretch
        )
        self.mods_widget.header().setStretchLastSection(False)

        def on_context_menu(point: qtc.QPoint):
            if not self.mods_widget.selectedItems():
                return

            # Get item at mouse position
            mod_selected = False
            plugin_selected = False
            mouse_pos = self.mods_widget.mapFromGlobal(qtg.QCursor.pos())
            mouse_pos.setY(mouse_pos.y() - self.mods_widget.header().height())
            current_item = self.mods_widget.itemAt(mouse_pos)

            if current_item is None:
                return

            if current_item.isDisabled():
                return
            if (
                qtc.Qt.ItemFlag.ItemIsUserCheckable in current_item.flags()
                and not current_item.text(2)
            ):
                selected_plugin = [
                    _plugin
                    for mod in self.mods
                    for _plugin in mod.plugins
                    if _plugin.tree_item == current_item
                ][0]
                plugin_selected = True
            else:
                matching = [
                    _mod
                    for _mod in self.mods
                    if _mod.tree_item == current_item
                    and not _mod.name.endswith("_separator")
                ]
                if matching:
                    selected_mod = matching[0]
                    mod_selected = True

            def show_strings():
                item = self.mods_widget.selectedItems()[0]
                if (
                    qtc.Qt.ItemFlag.ItemIsUserCheckable in item.flags()
                    and not item.text(2)
                ):
                    plugin = [
                        plugin
                        for mod in self.mods
                        for plugin in mod.plugins
                        if plugin.tree_item == item
                    ][0]

                    parser = PluginParser(plugin.path)
                    parser.parse_plugin()
                    strings = [
                        string
                        for group in parser.extract_strings().values()
                        for string in group
                    ]

                    dialog = StringListDialog(self.app, plugin.name, strings)
                    dialog.show()

            def check_selected():
                for item in self.mods_widget.selectedItems():
                    if (
                        qtc.Qt.ItemFlag.ItemIsUserCheckable in item.flags()
                        and not item.text(2)
                    ):
                        item.setCheckState(0, qtc.Qt.CheckState.Checked)

            def uncheck_selected():
                for item in self.mods_widget.selectedItems():
                    if (
                        qtc.Qt.ItemFlag.ItemIsUserCheckable in item.flags()
                        and not item.text(2)
                    ):
                        item.setCheckState(0, qtc.Qt.CheckState.Unchecked)

            def add_to_ignore_list():
                for item in self.mods_widget.selectedItems():
                    if (
                        qtc.Qt.ItemFlag.ItemIsUserCheckable in item.flags()
                        and not item.text(2)
                    ):
                        plugin_name = item.text(0).lower()
                        if plugin_name not in self.ignore_list:
                            self.ignore_list.append(plugin_name)

                self.save_ignore_list()
                self.update_modlist()

            def open_modpage():
                item = self.mods_widget.selectedItems()[0]
                matching = [_mod for _mod in self.mods if _mod.tree_item == item]
                if matching:
                    mod = matching[0]
                    if mod.mod_id:
                        url = utils.create_nexus_mods_url(
                            "skyrimspecialedition", mod.mod_id
                        )
                        os.startfile(url)

            def open_in_explorer():
                if mod_selected:
                    if selected_mod.path.is_dir():
                        os.system(f'explorer.exe "{selected_mod.path}"')
                elif plugin_selected:
                    if selected_plugin.path.is_file():
                        os.system(f'explorer.exe /select,"{selected_plugin.path}"')

            def show_translation_at_nm():
                if not plugin_selected and not mod_selected:
                    return

                if plugin_selected:
                    translation = self.app.database.get_translation_by_plugin_name(
                        selected_plugin.name
                    )
                else:
                    translation = self.app.database.get_translation_by_mod(selected_mod)

                if translation:
                    if translation.mod_id and translation.file_id:
                        url = utils.create_nexus_mods_url(
                            "skyrimspecialedition", translation.mod_id
                        )
                        os.startfile(url)
                else:
                    if plugin_selected:
                        mod = [
                            _mod
                            for _mod in self.mods
                            if selected_plugin in _mod.plugins
                        ][0]
                    else:
                        mod = selected_mod
                    translations = self.app.api.get_mod_translations(
                        "skyrimspecialedition", mod.mod_id
                    )
                    translation_urls = translations.get(
                        self.app.user_config["language"]
                    )
                    if translation_urls:
                        os.startfile(translation_urls[0])

            def show_untranslated_strings():
                if not plugin_selected:
                    return

                translation = self.app.database.get_translation_by_plugin_name(
                    selected_plugin.name
                )

                if translation is None:
                    return

                untranslated_strings = [
                    string
                    for string in translation.strings[selected_plugin.name.lower()]
                    if string.status == string.Status.TranslationRequired
                    or string.status == string.Status.TranslationIncomplete
                ]

                if untranslated_strings:
                    dialog = StringListDialog(
                        self.app, translation.name, untranslated_strings
                    )
                    dialog.show()

            def show_translation_strings():
                if not plugin_selected and not mod_selected:
                    return

                if plugin_selected:
                    translation = self.app.database.get_translation_by_plugin_name(
                        selected_plugin.name
                    )
                else:
                    translation = self.app.database.get_translation_by_mod(selected_mod)

                if translation:
                    strings = [
                        string
                        for plugin_strings in translation.strings.values()
                        for string in plugin_strings
                    ]

                    dialog = StringListDialog(self.app, translation.name, strings, True)
                    dialog.show()

            def show_translation():
                if not plugin_selected and not mod_selected:
                    return

                if plugin_selected:
                    translation = self.app.database.get_translation_by_plugin_name(
                        selected_plugin.name
                    )
                else:
                    translation = self.app.database.get_translation_by_mod(selected_mod)

                if translation:
                    translations_widget = (
                        self.database_widget.translations_widget.translations_widget
                    )
                    translations_widget.selectionModel().select(
                        translations_widget.indexFromItem(translation.tree_item),
                        qtc.QItemSelectionModel.SelectionFlag.Rows
                        | qtc.QItemSelectionModel.SelectionFlag.ClearAndSelect,
                    )
                    translations_widget.scrollToItem(
                        translation.tree_item,
                        qtw.QTreeWidget.ScrollHint.PositionAtCenter,
                    )

            def create_translation():
                if plugin_selected:
                    if not self.app.database.get_translation_by_plugin_name(
                        selected_plugin.name
                    ):

                        def process(ldialog: LoadingDialog):
                            ldialog.updateProgress(
                                text1=self.loc.main.creating_translation
                            )

                            global translation
                            translation = self.app.database.create_translation(
                                selected_plugin.path
                            )
                            translation.save_translation()
                            self.app.database.add_translation(translation)

                        loadingdialog = LoadingDialog(self.app.root, self.app, process)
                        loadingdialog.exec()

                        self.app.database.save_database()
                        self.database_widget.translations_widget.load_translations()
                        self.database_widget.translations_widget.translations_widget.scrollToItem(
                            translation.tree_item,
                            qtw.QTreeWidget.ScrollHint.PositionAtCenter,
                        )
                        selected_plugin.status = (
                            utils.Plugin.Status.TranslationIncomplete
                        )
                        self.update_modlist()
                        self.app.translation_editor.open_translation(translation)
                        self.app.tab_widget.setCurrentWidget(
                            self.app.translation_editor
                        )

            def import_as_translation():
                mod = [
                    _mod
                    for _mod in self.mods
                    if _mod.tree_item == current_item.parent()
                ][0]

                def process(ldialog: LoadingDialog):
                    ldialog.updateProgress(
                        text1=self.loc.main.importing_installed_translation
                    )
                    Processor.import_translation(
                        self.mods, mod, self.app, ignore_translation_status=True
                    )

                loadingdialog = LoadingDialog(self.app.root, self.app, process)
                loadingdialog.exec()

                self.app.database.save_database()
                self.app.mainpage_widget.database_widget.translations_widget.load_translations()
                self.update_modlist()

                messagebox = qtw.QMessageBox(self.app.root)
                messagebox.setWindowTitle(self.loc.main.success)
                messagebox.setText(self.loc.database.translation_imported)
                utils.apply_dark_title_bar(messagebox)
                messagebox.exec()

            def edit_translation():
                if not plugin_selected and not mod_selected:
                    return

                if plugin_selected:
                    translation = self.app.database.get_translation_by_plugin_name(
                        selected_plugin.name
                    )
                else:
                    translation = self.app.database.get_translation_by_mod(selected_mod)

                if translation:
                    self.app.translation_editor.open_translation(translation)
                    self.app.tab_widget.setCurrentIndex(1)

            menu = qtw.QMenu()

            expand_all_action = menu.addAction(self.loc.main.expand_all)
            expand_all_action.setIcon(
                qta.icon("mdi6.arrow-expand-vertical", color="#ffffff")
            )
            expand_all_action.triggered.connect(self.mods_widget.expandAll)

            collapse_all_action = menu.addAction(self.loc.main.collapse_all)
            collapse_all_action.setIcon(
                qta.icon("mdi6.arrow-collapse-vertical", color="#ffffff")
            )
            collapse_all_action.triggered.connect(self.mods_widget.collapseAll)

            show_translation_actions = False
            if mod_selected:
                if self.app.database.get_translation_by_mod(selected_mod):
                    show_translation_actions = True
            elif plugin_selected:
                if self.app.database.get_translation_by_plugin_name(
                    selected_plugin.name
                ):
                    show_translation_actions = True

            if show_translation_actions:
                menu.addSeparator()

                if plugin_selected:
                    if (
                        selected_plugin.status
                        == utils.Plugin.Status.TranslationIncomplete
                    ):
                        show_untranslated_strings_action = menu.addAction(
                            self.mloc.show_untranslated_strings
                        )
                        show_untranslated_strings_action.setIcon(
                            qta.icon("mdi6.book-alert-outline", color="#ffffff")
                        )
                        show_untranslated_strings_action.triggered.connect(
                            show_untranslated_strings
                        )

                show_translation_action = menu.addAction(self.mloc.show_translation)
                show_translation_action.setIcon(
                    qta.icon("mdi6.translate", color="#ffffff")
                )
                show_translation_action.triggered.connect(show_translation)

                show_translation_strings_action = menu.addAction(
                    self.loc.main.show_translation_strings
                )
                show_translation_strings_action.setIcon(
                    qta.icon("mdi6.book-open-outline", color="#ffffff")
                )
                show_translation_strings_action.triggered.connect(
                    show_translation_strings
                )

                show_translation_at_nm_action = menu.addAction(
                    self.loc.main.open_translation_on_nexusmods
                )
                show_translation_at_nm_action.setIcon(
                    qtg.QIcon(str(self.app.data_path / "icons" / "nexus_mods.svg"))
                )
                show_translation_at_nm_action.triggered.connect(show_translation_at_nm)

                edit_translation_action = menu.addAction(self.mloc.edit_translation)
                edit_translation_action.setIcon(
                    qta.icon("mdi6.text-box-edit", color="#ffffff")
                )
                edit_translation_action.triggered.connect(edit_translation)

            elif plugin_selected:
                menu.addSeparator()

                create_translation_action = menu.addAction(self.mloc.create_translation)
                create_translation_action.setIcon(
                    qta.icon("mdi6.passport-plus", color="#ffffff")
                )
                create_translation_action.triggered.connect(create_translation)
                create_translation_action.setDisabled(
                    selected_plugin.status == utils.Plugin.Status.NoneStatus
                    or selected_plugin.status == utils.Plugin.Status.NoStrings
                    or selected_plugin.status
                    == utils.Plugin.Status.TranslationInstalled
                )

                plugin_count = len(
                    [
                        plugin
                        for mod in self.mods
                        for plugin in mod.plugins
                        if plugin.name.lower() == selected_plugin.name.lower()
                    ]
                )
                if plugin_count > 1:
                    import_as_translation_action = menu.addAction(
                        self.mloc.import_as_translation
                    )
                    import_as_translation_action.setIcon(
                        qta.icon("mdi6.database-import-outline", color="#ffffff")
                    )
                    import_as_translation_action.triggered.connect(
                        import_as_translation
                    )

            if plugin_selected:
                menu.addSeparator()

                show_strings_action = menu.addAction(self.loc.main.show_strings)
                show_strings_action.setIcon(
                    qta.icon("mdi6.book-open-outline", color="#ffffff")
                )
                show_strings_action.triggered.connect(show_strings)

                add_to_ignore_list_action = menu.addAction(self.mloc.add_to_ignore_list)
                add_to_ignore_list_action.setIcon(
                    qta.icon("mdi.playlist-remove", color="#ffffff")
                )
                add_to_ignore_list_action.triggered.connect(add_to_ignore_list)

            menu.addSeparator()

            uncheck_action = menu.addAction(self.mloc.uncheck_selected)
            uncheck_action.setIcon(qta.icon("fa.close", color="#ffffff"))
            uncheck_action.triggered.connect(uncheck_selected)

            check_action = menu.addAction(self.mloc.check_selected)
            check_action.setIcon(qta.icon("fa.check", color="#ffffff"))
            check_action.triggered.connect(check_selected)

            menu.addSeparator()

            if plugin_selected:
                open_action = menu.addAction(self.loc.main.open)
                open_action.setIcon(
                    qta.icon("fa5s.external-link-alt", color="#ffffff")
                )
                open_action.triggered.connect(lambda: os.startfile(selected_plugin.path))

            if mod_selected:
                open_modpage_action = menu.addAction(self.loc.main.open_on_nexusmods)
                open_modpage_action.setIcon(
                    qtg.QIcon(str(self.app.data_path / "icons" / "nexus_mods.svg"))
                )
                open_modpage_action.triggered.connect(open_modpage)
                open_modpage_action.setDisabled(selected_mod.mod_id == 0)

            open_in_explorer_action = menu.addAction(self.loc.main.open_in_explorer)
            open_in_explorer_action.setIcon(qta.icon("fa5s.folder", color="#ffffff"))
            open_in_explorer_action.triggered.connect(open_in_explorer)

            menu.exec(self.mods_widget.mapToGlobal(point), at=expand_all_action)

        self.mods_widget.setContextMenuPolicy(
            qtc.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.mods_widget.customContextMenuRequested.connect(on_context_menu)

        self.database_widget = DatabaseWidget(self.app)
        self.database_widget.downloads_widget.download_finished.connect(
            self.update_modlist
        )
        splitter.addWidget(self.database_widget)

        self.search_box.textChanged.connect(
            lambda text: self.database_widget.translations_widget.update_translations()
        )
        self.search_box.returnPressed.connect(
            self.database_widget.translations_widget.update_translations
        )

        splitter.setSizes([0.8 * splitter.width(), 0.2 * splitter.width()])

        self.mods_widget.resizeColumnToContents(2)

    def update_modlist(self):
        """
        Updates visible modlist.
        """

        cur_search = self.search_box.text().lower()

        ignore_list = (
            self.ignore_list
            + utils.constants.BASE_GAME_PLUGINS
            + utils.constants.AE_CC_PLUGINS
            + [
                plugin
                for plugin, masterlist_entry in self.app.masterlist.items()
                if masterlist_entry["type"] == "ignore"
            ]
        )

        global none_status_plugins
        global no_strings_plugins
        global translation_installed_plugins
        global translation_available_plugins
        global translation_incomplete_plugins
        global requires_translation_plugins
        global no_translation_available_plugins

        none_status_plugins = 0
        no_strings_plugins = 0
        translation_installed_plugins = 0
        translation_available_plugins = 0
        translation_incomplete_plugins = 0
        requires_translation_plugins = 0
        no_translation_available_plugins = 0

        def process_mod_item(mod_item: qtw.QTreeWidgetItem) -> bool:
            global none_status_plugins
            global no_strings_plugins
            global translation_installed_plugins
            global translation_available_plugins
            global translation_incomplete_plugins
            global requires_translation_plugins
            global no_translation_available_plugins

            mod_visible = (
                cur_search in mod_item.text(0).lower()
                if cur_search
                else not mod_item.childCount() and self.filter_none.isChecked()
            )

            mod = [_mod for _mod in self.mods if _mod.tree_item == mod_item][0]

            for plugin in mod.plugins:
                plugin_visible = cur_search in plugin.name.lower()

                if plugin.name.lower() in ignore_list:
                    plugin.status = plugin.Status.NoneStatus
                    plugin.tree_item.setCheckState(0, qtc.Qt.CheckState.Unchecked)
                    plugin.tree_item.setDisabled(True)
                else:
                    plugin.tree_item.setDisabled(False)

                if self.app.database.get_translation_by_plugin_name(plugin.name):
                    if (
                        plugin.status != plugin.Status.TranslationIncomplete
                        and plugin.status != plugin.Status.IsTranslated
                    ):
                        plugin.status = plugin.Status.TranslationInstalled

                elif (
                    plugin.status == plugin.Status.TranslationInstalled
                    or plugin.status == plugin.Status.TranslationIncomplete
                ):
                    plugin.status = plugin.Status.RequiresTranslation

                # Hide/Show plugin according to status filter
                if plugin_visible:
                    match plugin.status:
                        case plugin.Status.NoneStatus:
                            plugin_visible = self.filter_none.isChecked()
                        case plugin.Status.NoStrings:
                            plugin_visible = self.filter_no_strings.isChecked()
                        case plugin.Status.IsTranslated:
                            plugin_visible = (
                                self.filter_translation_installed.isChecked()
                            )
                        case plugin.Status.TranslationInstalled:
                            plugin_visible = (
                                self.filter_translation_installed.isChecked()
                            )
                        case plugin.Status.TranslationAvailableInDatabase:
                            plugin_visible = (
                                self.filter_translation_available.isChecked()
                            )
                        case plugin.Status.TranslationAvailableAtNexusMods:
                            plugin_visible = (
                                self.filter_translation_available.isChecked()
                            )
                        case plugin.Status.RequiresTranslation:
                            plugin_visible = (
                                self.filter_requires_translation.isChecked()
                            )
                        case plugin.Status.NoTranslationAvailable:
                            plugin_visible = (
                                self.filter_no_translation_available.isChecked()
                            )

                ### Update counters
                # This is separate from above because the counters should only
                # be increased if the plugin is visible at all
                if plugin_visible:
                    match plugin.status:
                        case plugin.Status.NoneStatus:
                            none_status_plugins += 1
                        case plugin.Status.NoStrings:
                            no_strings_plugins += 1
                        case plugin.Status.IsTranslated:
                            translation_installed_plugins += 1
                        case plugin.Status.TranslationInstalled:
                            translation_installed_plugins += 1
                        case plugin.Status.TranslationIncomplete:
                            translation_incomplete_plugins += 1
                        case plugin.Status.TranslationAvailableInDatabase:
                            translation_available_plugins += 1
                        case plugin.Status.TranslationAvailableAtNexusMods:
                            translation_available_plugins += 1
                        case plugin.Status.RequiresTranslation:
                            requires_translation_plugins += 1
                        case plugin.Status.NoTranslationAvailable:
                            no_translation_available_plugins += 1

                plugin.tree_item.setHidden(not plugin_visible)

                if plugin_visible:
                    mod_visible = True

            mod_item.setHidden(not mod_visible)

            return mod_visible

        for toplevel_index in range(self.mods_widget.topLevelItemCount()):
            toplevel_item = self.mods_widget.topLevelItem(toplevel_index)

            is_mod = bool(
                [_mod for _mod in self.mods if _mod.tree_item == toplevel_item]
            )
            if is_mod:
                mod = [_mod for _mod in self.mods if _mod.tree_item == toplevel_item][0]
                is_mod = not mod.name.endswith("_separator")

            if is_mod:
                mod_item = toplevel_item
                process_mod_item(mod_item)

            else:
                separator_item = toplevel_item
                separator_visible = (
                    cur_search in separator_item.text(0).lower()
                    if cur_search
                    else (
                        not separator_item.childCount() and self.filter_none.isChecked()
                    )
                )

                for mod_index in range(separator_item.childCount()):
                    mod_item = separator_item.child(mod_index)

                    if process_mod_item(mod_item):
                        separator_visible = True

                separator_item.setHidden(not separator_visible)

        if self.mods_widget.selectedItems():
            self.mods_widget.scrollToItem(
                self.mods_widget.selectedItems()[0],
                qtw.QTreeWidget.ScrollHint.PositionAtCenter,
            )

        self.plugins_num_label.display(
            none_status_plugins
            + no_strings_plugins
            + translation_installed_plugins
            + translation_incomplete_plugins
            + translation_available_plugins
            + requires_translation_plugins
            + no_translation_available_plugins
        )

        num_tooltip = f"""
<table cellspacing="5">
<tr><td>{self.mloc.none_status}:\
</td><td align=right>{none_status_plugins}</td></tr>

<tr><td>{self.mloc.no_strings}:\
</td><td align=right>{no_strings_plugins}</td></tr>

<tr><td><font color="{utils.Plugin.Status.get_color(
    utils.Plugin.Status.TranslationInstalled
).name()}">{self.mloc.translation_installed}:\
</font></td><td align=right><font color="{utils.Plugin.Status.get_color(
    utils.Plugin.Status.TranslationInstalled
).name()}">{translation_installed_plugins}</font></td></tr>

<tr><td><font color="{utils.Plugin.Status.get_color(
    utils.Plugin.Status.TranslationAvailableAtNexusMods
).name()}">{self.mloc.translation_available}:\
</font></td><td align=right><font color="{utils.Plugin.Status.get_color(
    utils.Plugin.Status.TranslationAvailableAtNexusMods
).name()}">{translation_available_plugins}</font></td></tr>

<tr><td><font color="{utils.Plugin.Status.get_color(
    utils.Plugin.Status.TranslationIncomplete
).name()}">{self.mloc.translation_incomplete}:\
</font></td><td align=right><font color="{utils.Plugin.Status.get_color(
    utils.Plugin.Status.TranslationIncomplete
).name()}">{translation_incomplete_plugins}</font></td></tr>

<tr><td><font color="{utils.Plugin.Status.get_color(
    utils.Plugin.Status.RequiresTranslation
).name()}">{self.mloc.requires_translation}:\
</font></td><td align=right><font color="{utils.Plugin.Status.get_color(
    utils.Plugin.Status.RequiresTranslation
).name()}">{requires_translation_plugins}</font></td></tr>

<tr><td><font color="{utils.Plugin.Status.get_color(
    utils.Plugin.Status.NoTranslationAvailable
).name()}">{self.mloc.no_translation_available}:\
</font></td><td align=right><font color="{utils.Plugin.Status.get_color(
    utils.Plugin.Status.NoTranslationAvailable
).name()}">{no_translation_available_plugins}</font></td></tr>
</table>
"""
        self.plugins_num_label.setToolTip(num_tooltip)

        Processor.update_status_colors(self.mods)

    def load_mods(self):
        """
        Loads modlist from mod manager and displays mods on screen.
        """

        self.app.log.info("Loading mods...")

        def process(ldialog: LoadingDialog):
            global user_modinstance, modlist

            ldialog.updateProgress(text1=self.loc.main.loading_mods)

            user_mod_manager = self.app.user_config["mod_manager"]
            user_modinstance = self.app.user_config["modinstance"]
            instance_profile = self.app.user_config.get("instance_profile")

            for mod_manager in SUPPORTED_MOD_MANAGERS:
                if mod_manager.name.lower() == user_mod_manager.lower():
                    user_mod_manager = mod_manager
                    break
            else:
                raise KeyError(f"No mod manager {user_mod_manager!r} supported!")

            user_mod_manager = user_mod_manager()
            mod_instances = user_mod_manager.get_instances()
            if user_modinstance not in mod_instances:
                raise KeyError(f"No modinstance {user_modinstance!r} found!")

            modlist = user_mod_manager.get_modlist(user_modinstance, instance_profile)

        loadingdialog = LoadingDialog(self.app.root, self.app, process)
        loadingdialog.exec()

        ignore_list_path = self.app.data_path / "user" / "ignore_list.json"
        if ignore_list_path.is_file():
            with ignore_list_path.open(encoding="utf8") as ignore_list_file:
                self.ignore_list: list[str] = json.load(ignore_list_file)
        else:
            self.ignore_list = []

        ignore_list = (
            self.ignore_list
            + utils.constants.BASE_GAME_PLUGINS
            + utils.constants.AE_CC_PLUGINS
            + [
                plugin
                for plugin, masterlist_entry in self.app.masterlist.items()
                if masterlist_entry["type"] == "ignore"
            ]
        )

        self.mods_widget.clear()
        self.plugins_num_label.display(0)

        cur_separator: qtw.QTreeWidgetItem = None

        for i, mod in enumerate(modlist):
            if mod.name.endswith("_separator"):
                cur_separator = qtw.QTreeWidgetItem(
                    [
                        mod.name.removesuffix("_separator"),
                        "",
                        str(i + 1),  # Mod Priority
                    ]
                )
                cur_separator.setTextAlignment(0, qtc.Qt.AlignmentFlag.AlignCenter)
                cur_separator.setTextAlignment(2, qtc.Qt.AlignmentFlag.AlignCenter)
                font = qtg.QFont()
                font.setBold(True)
                font.setItalic(True)
                cur_separator.setFont(0, font)
                cur_separator.setFlags(qtc.Qt.ItemFlag.ItemIsSelectable)
                cur_separator.setToolTip(0, cur_separator.text(0))
                cur_separator.setDisabled(False)
                mod.tree_item = cur_separator
                self.mods_widget.addTopLevelItem(cur_separator)
            else:
                mod_item = qtw.QTreeWidgetItem(
                    [
                        mod.name,
                        mod.version,
                        str(i + 1),  # Mod Priority
                    ]
                )
                mod_item.setToolTip(0, mod_item.text(0))
                mod_item.setDisabled(False)
                mod_item.setTextAlignment(1, qtc.Qt.AlignmentFlag.AlignCenter)
                mod_item.setTextAlignment(2, qtc.Qt.AlignmentFlag.AlignCenter)
                mod.tree_item = mod_item

                if mod.plugins:
                    for plugin in mod.plugins:
                        plugin_item = qtw.QTreeWidgetItem(
                            [
                                plugin.name,
                                "",  # Version
                                "",  # Priority
                            ]
                        )
                        plugin_item.setToolTip(0, plugin_item.text(0))
                        plugin_item.setFlags(
                            qtc.Qt.ItemFlag.ItemIsUserCheckable
                            | qtc.Qt.ItemFlag.ItemIsSelectable
                        )
                        plugin.tree_item = plugin_item
                        if any(
                            entry_name.lower() == plugin.name.lower()
                            for entry_name in ignore_list
                        ):
                            plugin_item.setCheckState(0, qtc.Qt.CheckState.Unchecked)
                            plugin_item.setDisabled(True)
                        else:
                            plugin_item.setCheckState(0, qtc.Qt.CheckState.Checked)
                            plugin_item.setDisabled(False)
                        mod_item.addChild(plugin_item)

                if cur_separator is not None:
                    cur_separator.addChild(mod_item)
                else:
                    self.mods_widget.addTopLevelItem(mod_item)

        self.mods_widget.resizeColumnToContents(1)

        self.mods = modlist

        instance_profile = self.app.user_config.get("instance_profile")
        if instance_profile and instance_profile != "Default":
            self.title_label.setText(f"{user_modinstance} > {instance_profile}")
        else:
            self.title_label.setText(user_modinstance)
        self.update_modlist()

        self.app.log.info(f"Loaded {len(self.mods)} mod(s).")

    def open_ignore_list(self):
        """
        Opens Ignore List in a new Popup Dialog.
        """

        dialog = IgnoreListDialog(self.app.root, self.app)
        dialog.exec()

        self.save_ignore_list()
        self.update_modlist()

    def save_ignore_list(self):
        """
        Saves Ignore List to ignore_list.json.
        """

        ignore_list_path = self.app.data_path / "user" / "ignore_list.json"
        with ignore_list_path.open("w", encoding="utf8") as ignore_list_file:
            json.dump(self.ignore_list, ignore_list_file, indent=4)

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
        vlayout.addLayout(flayout)

        none_status_label = qtw.QLabel(self.mloc.none_status)
        flayout.addRow(none_status_label)

        no_strings_label = qtw.QLabel(self.mloc.no_strings)
        flayout.addRow(no_strings_label)

        translation_installed_color = qtw.QLabel()
        translation_installed_color.setPixmap(
            qta.icon(
                "mdi6.square-rounded",
                color=utils.Plugin.Status.get_color(
                    utils.Plugin.Status.TranslationInstalled
                ),
            ).pixmap(32, 32)
        )
        flayout.addRow(self.mloc.translation_installed, translation_installed_color)

        translation_available_color = qtw.QLabel()
        translation_available_color.setPixmap(
            qta.icon(
                "mdi6.square-rounded",
                color=utils.Plugin.Status.get_color(
                    utils.Plugin.Status.TranslationAvailableAtNexusMods
                ),
            ).pixmap(32, 32)
        )
        flayout.addRow(self.mloc.translation_available, translation_available_color)

        translation_incomplete_color = qtw.QLabel()
        translation_incomplete_color.setPixmap(
            qta.icon(
                "mdi6.square-rounded",
                color=utils.Plugin.Status.get_color(
                    utils.Plugin.Status.TranslationIncomplete
                ),
            ).pixmap(32, 32)
        )
        flayout.addRow(self.mloc.translation_incomplete, translation_incomplete_color)

        requires_translation_color = qtw.QLabel()
        requires_translation_color.setPixmap(
            qta.icon(
                "mdi6.square-rounded",
                color=utils.Plugin.Status.get_color(
                    utils.Plugin.Status.RequiresTranslation
                ),
            ).pixmap(32, 32)
        )
        flayout.addRow(self.mloc.requires_translation, requires_translation_color)

        no_translation_available_color = qtw.QLabel()
        no_translation_available_color.setPixmap(
            qta.icon(
                "mdi6.square-rounded",
                color=utils.Plugin.Status.get_color(
                    utils.Plugin.Status.NoTranslationAvailable
                ),
            ).pixmap(32, 32)
        )
        flayout.addRow(
            self.mloc.no_translation_available, no_translation_available_color
        )

        vlayout.addSpacing(25)

        ok_button = qtw.QPushButton(self.loc.main.ok)
        ok_button.clicked.connect(dialog.accept)
        vlayout.addWidget(ok_button)

        dialog.exec()
