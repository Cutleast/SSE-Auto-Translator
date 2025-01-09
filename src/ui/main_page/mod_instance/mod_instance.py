"""
Copyright (c) Cutleast
"""

import logging
import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHeaderView,
    QMessageBox,
    QPlainTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from app_context import AppContext
from core.cacher.cacher import Cacher
from core.config.app_config import AppConfig
from core.config.user_config import UserConfig
from core.database.database import TranslationDatabase
from core.database.string import String
from core.database.translation import Translation
from core.downloader.download_manager import DownloadManager
from core.downloader.translation_download import TranslationDownload
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.mod_instance.plugin import Plugin
from core.plugin_interface import plugin as esp
from core.scanner.scanner import Scanner
from core.translation_provider.source import Source
from core.utilities import matches_filter
from core.utilities.container_utils import join_dicts
from ui.utilities.tree_widget import are_children_visible
from ui.widgets.download_list_dialog import DownloadListDialog
from ui.widgets.loading_dialog import LoadingDialog
from ui.widgets.string_list.string_list_dialog import StringListDialog

from ..result_dialog import ResultDialog
from .help_dialog import ModInstanceHelpDialog
from .modinstance_menu import ModInstanceMenu


class ModInstanceWidget(QTreeWidget):
    """
    Widget for displaying the loaded modlist.
    """

    log: logging.Logger = logging.getLogger("ModInstance")

    cacher: Cacher
    database: TranslationDatabase
    user_config: UserConfig
    scanner: Scanner

    mod_instance: ModInstance
    """
    Currently loaded mod instance.
    """

    __mod_items: dict[Mod, QTreeWidgetItem]
    """
    Mapping of loaded mods to their tree items.
    """

    __plugin_items: dict[Mod, dict[Plugin, QTreeWidgetItem]]
    """
    Mapping of loaded mods to their plugin tree items.
    """

    __menu: ModInstanceMenu
    """
    Context menu.
    """

    __name_filter: Optional[tuple[str, bool]] = None
    """
    Optional name filter and case-sensitivity.
    """

    __state_filter: Optional[list[Plugin.Status]] = None
    """
    Optional list of plugin states to filter by.
    """

    def __init__(self) -> None:
        super().__init__()

        self.__init_ui()

        AppContext.get_app().ready_signal.connect(self.__post_init)

    def __post_init(self) -> None:
        self.cacher = AppContext.get_app().cacher
        self.database = AppContext.get_app().database
        self.user_config = AppContext.get_app().user_config
        self.scanner = AppContext.get_app().scanner
        self.mod_instance = AppContext.get_app().mod_instance

        self.database.update_signal.connect(self.update)
        self.mod_instance.update_signal.connect(self.__update)
        AppContext.get_app().exit_chain.append(self.__save_plugin_states)

        self.__load_mod_instance()

    def __init_ui(self) -> None:
        self.setUniformRowHeights(True)
        self.setAlternatingRowColors(True)
        self.resizeColumnToContents(2)
        self.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.itemDoubleClicked.connect(self.__item_double_clicked)
        self.setExpandsOnDoubleClick(False)

        self.__config_header()
        self.__init_context_menu()

    def __config_header(self) -> None:
        self.setHeaderLabels(
            [
                self.tr("Name"),
                self.tr("Version"),
                self.tr("Priority"),
            ]
        )
        self.header().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.header().setStretchLastSection(False)

    def __init_context_menu(self) -> None:
        self.__menu = ModInstanceMenu(self)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__menu.open)

    def __load_mod_instance(self) -> None:
        """
        Displays the loaded modlist.
        """

        self.__mod_items = {}
        self.__plugin_items = {}
        self.clear()

        checkstates: dict[Plugin, bool] = (
            self.mod_instance.load_plugin_states_from_cache()
        )

        cur_separator: Optional[QTreeWidgetItem] = None
        for i, mod in enumerate(self.mod_instance.mods):
            if mod.name.endswith("_separator"):
                cur_separator = ModInstanceWidget._create_separator_item(mod, i)
                self.__mod_items[mod] = cur_separator
                self.addTopLevelItem(cur_separator)
            else:
                mod_item: QTreeWidgetItem = ModInstanceWidget._create_mod_item(mod, i)

                self.__mod_items[mod] = mod_item
                self.__plugin_items[mod] = {
                    plugin: ModInstanceWidget._create_plugin_item(
                        plugin, checkstates[plugin]
                    )
                    for plugin in mod.plugins
                }
                mod_item.addChildren(list(self.__plugin_items[mod].values()))

                if cur_separator is not None:
                    cur_separator.addChild(mod_item)
                else:
                    self.addTopLevelItem(mod_item)

        self.resizeColumnToContents(1)
        self.__update()

    @staticmethod
    def _create_separator_item(separator: Mod, index: int) -> QTreeWidgetItem:
        separator_item = QTreeWidgetItem(
            [
                separator.name.removesuffix("_separator"),
                "",
                str(index + 1),  # Mod Priority
            ]
        )
        separator_item.setTextAlignment(0, Qt.AlignmentFlag.AlignCenter)
        separator_item.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setBold(True)
        font.setItalic(True)
        separator_item.setFont(0, font)
        separator_item.setFlags(Qt.ItemFlag.ItemIsSelectable)
        separator_item.setToolTip(0, separator_item.text(0))
        separator_item.setDisabled(False)

        return separator_item

    @staticmethod
    def _create_mod_item(mod: Mod, index: int) -> QTreeWidgetItem:
        mod_item = QTreeWidgetItem(
            [
                mod.name,
                mod.version,
                str(index + 1),  # Mod Priority
            ]
        )
        mod_item.setToolTip(0, mod_item.text(0))
        mod_item.setDisabled(False)
        mod_item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)
        mod_item.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)

        return mod_item

    @staticmethod
    def _create_plugin_item(plugin: Plugin, checked: bool = True) -> QTreeWidgetItem:
        plugin_item = QTreeWidgetItem(
            [
                plugin.name,
                "",  # Version
                "",  # Priority
            ]
        )
        plugin_item.setToolTip(0, plugin.name)
        plugin_item.setFlags(
            Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable
        )
        plugin_item.setDisabled(False)
        plugin_item.setCheckState(
            0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        )

        return plugin_item

    def __update(self) -> None:
        """
        Updates the displayed modlist.
        """

        name_filter: Optional[str] = (
            self.__name_filter[0] if self.__name_filter else None
        )
        case_sensitive: Optional[bool] = (
            self.__name_filter[1] if self.__name_filter else None
        )

        for mod, mod_item in self.__mod_items.items():
            plugin_items: dict[Plugin, QTreeWidgetItem] = self.__plugin_items.get(
                mod, {}
            )

            for plugin, item in plugin_items.items():
                item.setHidden(
                    (
                        self.__state_filter is not None
                        and plugin.status not in self.__state_filter
                    )
                    or not matches_filter(
                        plugin.name, name_filter, case_sensitive or False
                    )
                )
                item.setForeground(
                    0, Plugin.Status.get_color(plugin.status) or Qt.GlobalColor.white
                )

            mod_item.setHidden(
                (not are_children_visible(mod_item) and self.__state_filter is not None)
                or not matches_filter(mod.name, name_filter, case_sensitive or False)
            )
            mod_item.setForeground(
                0,
                Plugin.Status.get_color(
                    max(
                        [plugin.status for plugin in mod.plugins],
                        default=Plugin.Status.NoneStatus,
                    )
                )
                or Qt.GlobalColor.white,
            )

    def show_strings(self) -> None:
        """
        Show the strings of the current item.
        """

        current_item: Optional[Mod | Plugin] = self.get_current_item()

        if isinstance(current_item, Plugin):
            dialog = StringListDialog(
                current_item.name, self.cacher.get_plugin_strings(current_item.path)
            )
            dialog.show()

        elif isinstance(current_item, Mod):
            strings: dict[str, list[String]] = {}

            for plugin in current_item.plugins:
                plugin_strings = self.cacher.get_plugin_strings(plugin.path)
                strings[plugin.name] = plugin_strings

            dialog = StringListDialog(current_item.name, strings)
            dialog.show()

    def show_structure(self) -> None:
        # TODO: Overhaul this
        current_item: Optional[Mod | Plugin] = self.get_current_item()

        if isinstance(current_item, Plugin):
            plugin = esp.Plugin(current_item.path)

            text = str(plugin)
            self.log.debug(f"Text Length: {len(text)}")

            with open("debug.txt", "w", encoding="utf8") as file:
                file.write(text)

            self.log.debug("Written to 'debug.txt'.")

            dialog = QDialog(QApplication.activeModalWidget())
            dialog.setWindowTitle(current_item.name)
            dialog.setMinimumSize(1400, 800)

            vlayout = QVBoxLayout()
            dialog.setLayout(vlayout)

            textbox = QPlainTextEdit()
            textbox.setFont(QFont("Consolas"))
            textbox.setReadOnly(True)
            textbox.setPlainText(text)
            textbox.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            textbox.setCursor(Qt.CursorShape.IBeamCursor)
            textbox.setFocus()
            vlayout.addWidget(textbox)

            dialog.exec()

    def check_selected(self) -> None:
        for item in self.selectedItems():
            if Qt.ItemFlag.ItemIsUserCheckable in item.flags() and not item.text(2):
                item.setCheckState(0, Qt.CheckState.Checked)

    def uncheck_selected(self) -> None:
        for item in self.selectedItems():
            if Qt.ItemFlag.ItemIsUserCheckable in item.flags() and not item.text(2):
                item.setCheckState(0, Qt.CheckState.Unchecked)

    def add_to_ignore_list(self) -> None:
        _, selected_plugins = self.get_selected_items()

        for plugin in selected_plugins:
            plugin_name: str = plugin.name.lower()

            if plugin_name not in self.user_config.plugin_ignorelist:
                self.user_config.plugin_ignorelist.append(plugin_name)

        self.user_config.save()
        self.__update()

    def open_modpage(self) -> None:
        current_item: Optional[Mod | Plugin] = self.get_current_item()

        if isinstance(current_item, Mod) and current_item.mod_id:
            url: Optional[str] = AppContext.get_app().provider.get_modpage_link(
                current_item.mod_id, source=Source.NexusMods
            )

            if url is not None:
                os.startfile(url)

    def open_in_explorer(self) -> None:
        current_item: Optional[Mod | Plugin] = self.get_current_item()

        if isinstance(current_item, Mod):
            if current_item.path.is_dir():
                os.system(f'explorer.exe "{current_item.path}"')

        elif isinstance(current_item, Plugin):
            if current_item.path.is_file():
                os.system(f'explorer.exe /select,"{current_item.path}"')

    def show_untranslated_strings(self) -> None:
        current_item: Optional[Mod | Plugin] = self.get_current_item()
        translation: Optional[Translation] = None

        if current_item is None:
            return

        if isinstance(current_item, Plugin):
            translation = self.database.get_translation_by_plugin_name(
                current_item.name
            )

        elif isinstance(current_item, Mod):
            translation = self.database.get_translation_by_mod(current_item)

        if translation is not None:
            untranslated_strings: list[String] = [
                string
                for string in translation.strings[current_item.name.lower()]
                if string.status == string.Status.TranslationRequired
                or string.status == string.Status.TranslationIncomplete
            ]

            if untranslated_strings:
                dialog = StringListDialog(translation.name, untranslated_strings)
                dialog.show()

    def show_translation_strings(self) -> None:
        current_item: Optional[Mod | Plugin] = self.get_current_item()
        translation: Optional[Translation] = None

        if current_item is None:
            return

        if isinstance(current_item, Plugin):
            translation = self.database.get_translation_by_plugin_name(
                current_item.name
            )
        elif isinstance(current_item, Mod):
            translation = self.database.get_translation_by_mod(current_item)

        if translation is not None:
            dialog = StringListDialog(
                translation.name,
                translation.strings,
                show_translation=True,
            )
            dialog.show()

    def show_translation(self) -> None:
        current_item: Optional[Mod | Plugin] = self.get_current_item()
        translation: Optional[Translation] = None

        if current_item is None:
            return

        if isinstance(current_item, Plugin):
            translation = self.database.get_translation_by_plugin_name(
                current_item.name
            )
        elif isinstance(current_item, Mod):
            translation = self.database.get_translation_by_mod(current_item)

        self.database.highlight_signal.emit(translation)

    def create_translation(self) -> None:
        current_item: Optional[Mod | Plugin] = self.get_current_item()

        if isinstance(current_item, Plugin):
            translation: Optional[Translation] = (
                self.database.get_translation_by_plugin_name(current_item.name)
            )
            if translation is None:

                def process(ldialog: LoadingDialog) -> Translation:
                    ldialog.updateProgress(text1=self.tr("Creating translation..."))

                    return self.database.create_translation(current_item)

                translation = LoadingDialog.run_callable(
                    QApplication.activeModalWidget(), process
                )

                current_item.status = Plugin.Status.TranslationIncomplete

                self.database.highlight_signal.emit(translation)
                self.database.edit_signal.emit(translation)

        # TODO: Implement this for entire mods

    def import_as_translation(self) -> None:
        current_item: Optional[Mod | Plugin] = self.get_current_item()

        if isinstance(current_item, Mod):

            def process(ldialog: LoadingDialog) -> None:
                ldialog.updateProgress(
                    text1=self.tr("Importing installed translation...")
                )

                # TODO: Make the import dependent on the original plugins instead of a single mod
                # Find the original mod
                original_mod: Optional[Mod] = None
                for plugin in current_item.plugins:
                    original_mod = self.mod_instance.get_mod_with_plugin(
                        plugin.name,
                        ignore_mods=[current_item],
                        ignore_states=[
                            Plugin.Status.IsTranslated,
                            Plugin.Status.TranslationInstalled,
                        ],
                        ignore_case=True,
                    )

                    if original_mod is not None:
                        break

                if original_mod is not None:
                    self.database.importer.import_mod_as_translation(
                        current_item, original_mod
                    )
                else:
                    raise FileNotFoundError(
                        f"Could not find original mod for {current_item.name!r}"
                    )

            LoadingDialog.run_callable(QApplication.activeModalWidget(), process)

            messagebox = QMessageBox(QApplication.activeModalWidget())
            messagebox.setWindowTitle(self.tr("Success!"))
            messagebox.setText(
                self.tr("Translation successfully imported into database.")
            )
            messagebox.exec()

    def edit_translation(self) -> None:
        current_item: Optional[Mod | Plugin] = self.get_current_item()

        translation: Optional[Translation] = None
        if isinstance(current_item, Plugin):
            translation = self.database.get_translation_by_plugin_name(
                current_item.name
            )
        elif isinstance(current_item, Mod):
            translation = self.database.get_translation_by_mod(current_item)

        if translation is not None:
            self.database.edit_signal.emit(translation)

    def open_plugin(self) -> None:
        current_item: Optional[Mod | Plugin] = self.get_current_item()

        if isinstance(current_item, Plugin):
            os.startfile(current_item.path)

    def get_selected_items(self) -> tuple[list[Mod], list[Plugin]]:
        """
        Returns the currently selected items.

        Returns:
            tuple[list[Mod], list[Plugin]]: Selected mods and plugins
        """

        selected_mods: list[Mod] = [
            mod for mod, item in self.__mod_items.items() if item.isSelected()
        ]
        selected_plugins: list[Plugin] = [
            plugin
            for plugin_items in self.__plugin_items.values()
            for plugin, item in plugin_items.items()
            if item.isSelected()
        ]

        return selected_mods, selected_plugins

    def get_selected_plugins(self) -> dict[Mod, list[Plugin]]:
        """
        Returns the currently selected plugins.

        Returns:
            dict[Mod, list[Plugin]]: Mods with selected plugins
        """

        return {
            mod: [plugin for plugin in plugin_items.keys()]
            for mod, plugin_items in self.__plugin_items.items()
            for item in plugin_items.values()
            if item.isSelected()
        }

    def get_checked_items(self) -> dict[Mod, list[Plugin]]:
        """
        Returns the currently checked items.

        Returns:
            dict[Mod, list[Plugin]]: Mods with checked plugins
        """

        return {
            mod: [plugin for plugin in plugin_items.keys()]
            for mod, plugin_items in self.__plugin_items.items()
            for item in plugin_items.values()
            if item.checkState(0) == Qt.CheckState.Checked
        }

    def get_current_item(self) -> Optional[Mod | Plugin]:
        """
        Returns the item where the cursor is.

        Returns:
            Optional[Mod | Plugin]: Current item or None
        """

        item: Optional[Mod | Plugin] = None

        for mod in self.__mod_items:
            if self.__mod_items[mod].isSelected():
                item = mod
                break
            for plugin, plugin_item in self.__plugin_items.get(mod, {}).items():
                if plugin_item.isSelected():
                    item = plugin
                    break

        return item

    def __item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        current_item: Optional[Mod | Plugin] = self.get_current_item()

        if (
            current_item is not None
            and not (
                isinstance(current_item, Mod)
                and current_item.name.endswith("_separator")
            )
            and (
                not isinstance(current_item, Mod)
                or any(
                    plugin.status != Plugin.Status.NoStrings
                    for plugin in current_item.plugins
                )
            )
        ) and AppContext.get_app().app_config.show_strings_on_double_click:
            self.show_strings()
        else:
            item.setExpanded(not item.isExpanded())

    def basic_scan(self) -> None:
        selected_mods: list[Mod] = self.get_selected_items()[0]
        selected_plugins: dict[Mod, list[Plugin]] = self.get_selected_plugins()

        scan_result: dict[Plugin, Plugin.Status] = join_dicts(
            *LoadingDialog.run_callable(
                QApplication.activeModalWidget(),
                lambda ldialog: self.scanner.run_basic_scan(selected_plugins, ldialog),
            ).values()
        )
        self.mod_instance.set_plugin_states(scan_result)

        app_config: AppConfig = AppContext.get_app().app_config
        if app_config.auto_import_translations:
            LoadingDialog.run_callable(
                QApplication.activeModalWidget(),
                lambda ldialog: self.scanner.import_installed_translations(
                    selected_mods, ldialog
                ),
            )

        ResultDialog(
            self.mod_instance.get_plugin_state_summary(
                [plugin for plugins in selected_plugins.values() for plugin in plugins]
            ),
            QApplication.activeModalWidget(),
        ).exec()

    def online_scan(self) -> None:
        selected_plugins: dict[Mod, list[Plugin]] = self.get_selected_plugins()

        scan_result: dict[Plugin, Plugin.Status] = join_dicts(
            *LoadingDialog.run_callable(
                QApplication.activeModalWidget(),
                lambda ldialog: self.scanner.run_online_scan(selected_plugins, ldialog),
            ).values()
        )
        self.mod_instance.set_plugin_states(scan_result)

        ResultDialog(
            self.mod_instance.get_plugin_state_summary(
                [plugin for plugins in selected_plugins.values() for plugin in plugins]
            ),
            QApplication.activeModalWidget(),
        ).exec()

    def download_and_install_translations(self) -> None:
        download_manager: DownloadManager = AppContext.get_app().download_manager
        download_entries: dict[str, list[TranslationDownload]] = (
            LoadingDialog.run_callable(
                QApplication.activeModalWidget(),
                lambda ldialog: download_manager.collect_available_downloads(
                    self.get_selected_plugins(), ldialog
                ),
            )
        )

        DownloadListDialog(
            download_entries, parent=QApplication.activeModalWidget()
        ).exec()

    def build_output(self) -> None:
        output_path: Path = LoadingDialog.run_callable(
            QApplication.activeModalWidget(), self.database.exporter.build_output_mod
        )

        message_box = QMessageBox()
        message_box.setWindowTitle(self.tr("Success!"))
        message_box.setText(
            self.tr("Created output mod for DSD at: ") + str(output_path)
        )
        message_box.setStandardButtons(
            QMessageBox.StandardButton.Ok
            | QMessageBox.StandardButton.Help
            | QMessageBox.StandardButton.Open
        )
        message_box.button(QMessageBox.StandardButton.Ok).setText(self.tr("Ok"))
        message_box.button(QMessageBox.StandardButton.Help).setText(
            self.tr("Open output mod in Explorer")
        )
        btn = message_box.button(QMessageBox.StandardButton.Open)
        btn.setText(self.tr("Open DSD modpage on Nexus Mods"))
        btn.clicked.disconnect()
        btn.clicked.connect(
            lambda: os.startfile(
                "https://www.nexusmods.com/skyrimspecialedition/mods/107676"
            )
        )

        choice = message_box.exec()

        if choice == message_box.StandardButton.Help:
            os.startfile(output_path)

    def deep_scan(self) -> None:
        result: dict[Plugin, Plugin.Status] = LoadingDialog.run_callable(
            QApplication.activeModalWidget(), self.scanner.run_deep_scan
        )
        self.mod_instance.set_plugin_states(result)

        ResultDialog(
            self.mod_instance.get_plugin_state_summary(),
            QApplication.activeModalWidget(),
        ).exec()

    def show_help(self) -> None:
        """
        Displays help popup.
        """

        ModInstanceHelpDialog(QApplication.activeModalWidget()).exec()

    def set_name_filter(self, name_filter: tuple[str, bool]) -> None:
        """
        Sets the name filter.

        Args:
            name_filter (tuple[str, bool]): The name to filter by and case-sensitivity.
        """

        self.__name_filter = name_filter if name_filter[0].strip() else None
        self.__update()

    def set_state_filter(self, state_filter: list[Plugin.Status]) -> None:
        """
        Sets the state filter.

        Args:
            state_filter (list[Plugin.Status]): The states to filter by.
        """

        self.__state_filter = state_filter
        self.__update()

    def __save_plugin_states(self) -> None:
        plugin_states: dict[Plugin, bool] = {
            plugin: item.checkState(0) == Qt.CheckState.Checked
            for plugin_items in self.__plugin_items.values()
            for plugin, item in plugin_items.items()
        }

        cacher: Cacher = AppContext.get_app().cacher
        cacher.update_plugin_states_cache(plugin_states)
