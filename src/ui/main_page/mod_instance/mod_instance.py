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
from core.cache.cache import Cache
from core.config.app_config import AppConfig
from core.config.user_config import UserConfig
from core.database.database import TranslationDatabase
from core.database.string import String
from core.database.translation import Translation
from core.downloader.download_manager import DownloadManager
from core.downloader.translation_download import TranslationDownload
from core.masterlist.masterlist import Masterlist
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.mod_instance.state_service import StateService
from core.plugin_interface import plugin as esp
from core.scanner.scanner import Scanner
from core.translation_provider.exceptions import ModNotFoundError
from core.translation_provider.mod_id import ModId
from core.translation_provider.nm_api.nxm_handler import NXMHandler
from core.translation_provider.provider import Provider
from core.translation_provider.source import Source
from core.utilities import matches_filter
from core.utilities.container_utils import join_dicts
from core.utilities.exe_info import get_current_path
from ui.downloader.download_list_dialog import DownloadListDialog
from ui.utilities.tree_widget import are_children_visible
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

    cache: Cache
    database: TranslationDatabase
    app_config: AppConfig
    user_config: UserConfig
    masterlist: Masterlist
    scanner: Scanner
    provider: Provider
    download_manager: DownloadManager
    nxm_listener: NXMHandler

    mod_instance: ModInstance
    """
    Currently loaded mod instance.
    """

    state_service: StateService

    __mod_items: dict[Mod, QTreeWidgetItem]
    """
    Mapping of loaded mods to their tree items.
    """

    __modfile_items: dict[Mod, dict[ModFile, QTreeWidgetItem]]
    """
    Mapping of loaded mods to their mod file tree items.
    """

    __menu: ModInstanceMenu
    """
    Context menu.
    """

    __name_filter: Optional[tuple[str, bool]] = None
    """
    Optional name filter and case-sensitivity.
    """

    __state_filter: Optional[list[TranslationStatus]] = None
    """
    Optional list of mod file states to filter by.
    """

    def __init__(
        self,
        cache: Cache,
        database: TranslationDatabase,
        app_config: AppConfig,
        user_config: UserConfig,
        masterlist: Masterlist,
        scanner: Scanner,
        provider: Provider,
        download_manager: DownloadManager,
        nxm_listener: NXMHandler,
        mod_instance: ModInstance,
        state_service: StateService,
    ) -> None:
        super().__init__()

        self.cache = cache
        self.database = database
        self.app_config = app_config
        self.user_config = user_config
        self.masterlist = masterlist
        self.scanner = scanner
        self.provider = provider
        self.download_manager = download_manager
        self.nxm_listener = nxm_listener
        self.mod_instance = mod_instance
        self.state_service = state_service

        self.__init_ui()

        self.database.update_signal.connect(self.update)
        self.state_service.update_signal.connect(self.__update)
        AppContext.get_app().exit_chain.append(self.__save_modfile_states)

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
        self.__modfile_items = {}
        self.clear()

        checkstates: dict[ModFile, bool] = self.state_service.load_states_from_cache()

        cur_separator: Optional[QTreeWidgetItem] = None
        for i, mod in enumerate(self.mod_instance.mods):
            if mod.name.endswith("_separator"):
                cur_separator = ModInstanceWidget._create_separator_item(mod, i)
                self.__mod_items[mod] = cur_separator
                self.addTopLevelItem(cur_separator)
            else:
                mod_item: QTreeWidgetItem = ModInstanceWidget._create_mod_item(mod, i)

                self.__mod_items[mod] = mod_item
                self.__modfile_items[mod] = {
                    modfile: ModInstanceWidget._create_modfile_item(
                        modfile, checkstates[modfile]
                    )
                    for modfile in mod.modfiles
                }
                mod_item.addChildren(list(self.__modfile_items[mod].values()))

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
    def _create_modfile_item(modfile: ModFile, checked: bool = True) -> QTreeWidgetItem:
        modfile_item = QTreeWidgetItem(
            [
                modfile.name,
                "",  # Version
                "",  # Priority
            ]
        )
        modfile_item.setToolTip(0, modfile.name)
        modfile_item.setFlags(
            Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable
        )
        modfile_item.setDisabled(False)
        modfile_item.setCheckState(
            0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        )

        return modfile_item

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
            modfile_items: dict[ModFile, QTreeWidgetItem] = self.__modfile_items.get(
                mod, {}
            )

            for modfile, item in modfile_items.items():
                ignored: bool = self.masterlist.is_ignored(modfile.name)
                item.setDisabled(ignored)
                if ignored:
                    item.setCheckState(0, Qt.CheckState.Unchecked)

                item.setHidden(
                    (
                        self.__state_filter is not None
                        and modfile.status not in self.__state_filter
                    )
                    or not matches_filter(
                        modfile.name, name_filter, case_sensitive or False
                    )
                )
                item.setForeground(
                    0,
                    TranslationStatus.get_color(modfile.status) or Qt.GlobalColor.white,
                )

            mod_item.setHidden(
                (self.__state_filter is not None and not are_children_visible(mod_item))
                or (
                    not matches_filter(mod.name, name_filter, case_sensitive or False)
                    and not are_children_visible(mod_item)
                )
            )
            mod_item.setForeground(
                0,
                TranslationStatus.get_color(
                    max(
                        [modfile.status for modfile in mod.modfiles],
                        default=TranslationStatus.NoneStatus,
                    )
                )
                or Qt.GlobalColor.white,
            )

    def show_strings(self) -> None:
        """
        Show the strings of the current item.
        """

        current_item: Optional[Mod | ModFile] = self.get_current_item()

        if isinstance(current_item, ModFile):
            dialog = StringListDialog(
                current_item.name, current_item.get_strings(self.cache)
            )
            dialog.show()

        elif isinstance(current_item, Mod):
            strings: dict[str, list[String]] = {}

            for modfile in current_item.modfiles:
                modfile_strings = modfile.get_strings(self.cache)
                strings[modfile.name] = modfile_strings

            dialog = StringListDialog(current_item.name, strings)
            dialog.show()

    def show_structure(self) -> None:
        # TODO: Overhaul this
        current_item: Optional[Mod | ModFile] = self.get_current_item()

        if isinstance(current_item, ModFile):
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
        _, selected_modfiles = self.get_selected_items()

        for modfile in selected_modfiles:
            self.masterlist.add_to_ignore_list(modfile.name)

        self.user_config.save()
        self.__update()

    def open_modpage(self) -> None:
        current_item: Optional[Mod | ModFile] = self.get_current_item()

        if isinstance(current_item, Mod) and current_item.mod_id:
            try:
                url: Optional[str] = self.provider.get_modpage_url(
                    current_item.mod_id, source=Source.NexusMods
                )
                os.startfile(url)
            except ModNotFoundError:
                pass

    def open_in_explorer(self) -> None:
        current_item: Optional[Mod | ModFile] = self.get_current_item()

        if isinstance(current_item, Mod):
            if current_item.path.is_dir():
                os.system(f'explorer.exe "{current_item.path}"')

        elif isinstance(current_item, ModFile):
            if current_item.path.is_file():
                os.system(f'explorer.exe /select,"{current_item.path}"')

    def show_untranslated_strings(self) -> None:
        current_item: Optional[Mod | ModFile] = self.get_current_item()
        translation: Optional[Translation] = None

        if current_item is None:
            return

        if isinstance(current_item, ModFile):
            translation = self.database.get_translation_by_modfile_name(
                current_item.name
            )

        else:
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
        current_item: Optional[Mod | ModFile] = self.get_current_item()
        translation: Optional[Translation] = None

        if current_item is None:
            return

        if isinstance(current_item, ModFile):
            translation = self.database.get_translation_by_modfile_name(
                current_item.name
            )
        else:
            translation = self.database.get_translation_by_mod(current_item)

        if translation is not None:
            dialog = StringListDialog(
                translation.name,
                translation.strings,
                show_translation=True,
            )
            dialog.show()

    def show_translation(self) -> None:
        current_item: Optional[Mod | ModFile] = self.get_current_item()
        translation: Optional[Translation] = None

        if current_item is None:
            return

        if isinstance(current_item, ModFile):
            translation = self.database.get_translation_by_modfile_name(
                current_item.name
            )
        else:
            translation = self.database.get_translation_by_mod(current_item)

        self.database.highlight_signal.emit(translation)

    def create_translation(self) -> None:
        current_item: Optional[Mod | ModFile] = self.get_current_item()

        if isinstance(current_item, ModFile):
            translation: Optional[Translation] = (
                self.database.get_translation_by_modfile_name(current_item.name)
            )
            if translation is None:

                def process(ldialog: LoadingDialog) -> Translation:
                    ldialog.updateProgress(text1=self.tr("Creating translation..."))

                    return self.database.create_translation(current_item)

                translation = LoadingDialog.run_callable(
                    QApplication.activeModalWidget(), process
                )

                current_item.status = TranslationStatus.TranslationIncomplete

                self.database.highlight_signal.emit(translation)
                self.database.edit_signal.emit(translation)

        # TODO: Implement this for entire mods

    def import_as_translation(self) -> None:
        current_item: Optional[Mod | ModFile] = self.get_current_item()

        if isinstance(current_item, Mod):

            def process(ldialog: LoadingDialog) -> None:
                ldialog.updateProgress(
                    text1=self.tr("Importing installed translation...")
                )

                # TODO: Make the import dependent on the original mod files instead of a single mod
                # Find the original mod
                original_mod: Optional[Mod] = None
                for modfile in current_item.modfiles:
                    original_mod = self.mod_instance.get_mod_with_modfile(
                        modfile.name,
                        ignore_mods=[current_item],
                        ignore_states=[
                            TranslationStatus.IsTranslated,
                            TranslationStatus.TranslationInstalled,
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
        current_item: Optional[Mod | ModFile] = self.get_current_item()

        translation: Optional[Translation] = None
        if isinstance(current_item, ModFile):
            translation = self.database.get_translation_by_modfile_name(
                current_item.name
            )
        elif isinstance(current_item, Mod):
            translation = self.database.get_translation_by_mod(current_item)

        if translation is not None:
            self.database.edit_signal.emit(translation)

    def open_modfile(self) -> None:
        current_item: Optional[Mod | ModFile] = self.get_current_item()

        if isinstance(current_item, ModFile):
            os.startfile(current_item.path)

    def get_selected_items(self) -> tuple[list[Mod], list[ModFile]]:
        """
        Returns the currently selected items.

        Returns:
            tuple[list[Mod], list[ModFile]]: Selected mods and mod files
        """

        selected_mods: list[Mod] = [
            mod for mod, item in self.__mod_items.items() if item.isSelected()
        ]
        selected_modfiles: list[ModFile] = [
            modfile
            for modfile_items in self.__modfile_items.values()
            for modfile, item in modfile_items.items()
            if item.isSelected()
        ]

        return selected_mods, selected_modfiles

    def get_selected_modfiles(self) -> dict[Mod, list[ModFile]]:
        """
        Returns the currently selected mod files.

        Returns:
            dict[Mod, list[ModFile]]: Mods with selected mod files
        """

        return {
            mod: [
                modfile for modfile, item in modfile_items.items() if item.isSelected()
            ]
            for mod, modfile_items in self.__modfile_items.items()
            if any(item.isSelected() for item in modfile_items.values())
        }

    def get_checked_items(self) -> dict[Mod, list[ModFile]]:
        """
        Returns the currently checked items.

        Returns:
            dict[Mod, list[ModFile]]: Mods with checked mod files
        """

        return {
            mod: [
                modfile
                for modfile, item in modfile_items.items()
                if item.checkState(0) == Qt.CheckState.Checked
            ]
            for mod, modfile_items in self.__modfile_items.items()
            if any(
                item.checkState(0) == Qt.CheckState.Checked
                for item in modfile_items.values()
            )
        }

    def get_current_item(self) -> Optional[Mod | ModFile]:
        """
        Returns the item where the cursor is.

        Returns:
            Optional[Mod | ModFile]: Current item or None
        """

        item: Optional[Mod | ModFile] = None

        for mod in self.__mod_items:
            if self.__mod_items[mod].isSelected():
                item = mod
                break
            for modfile, modfile_item in self.__modfile_items.get(mod, {}).items():
                if modfile_item.isSelected():
                    item = modfile
                    break

        return item

    def __item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        current_item: Optional[Mod | ModFile] = self.get_current_item()

        if (
            current_item is not None
            and not (
                isinstance(current_item, Mod)
                and current_item.name.endswith("_separator")
            )
            and (
                not isinstance(current_item, Mod)
                or any(
                    modfile.status != TranslationStatus.NoStrings
                    for modfile in current_item.modfiles
                )
            )
        ) and self.app_config.show_strings_on_double_click:
            self.show_strings()
        else:
            item.setExpanded(not item.isExpanded())

    def basic_scan(self) -> None:
        selected_mods: list[Mod] = self.get_selected_items()[0]
        selected_modfiles: dict[Mod, list[ModFile]] = self.get_selected_modfiles()

        scan_result: dict[ModFile, TranslationStatus] = join_dicts(
            *LoadingDialog.run_callable(
                QApplication.activeModalWidget(),
                lambda ldialog: self.scanner.run_basic_scan(selected_modfiles, ldialog),
            ).values()
        )
        self.state_service.set_modfile_states(scan_result)

        if self.app_config.auto_import_translations:
            LoadingDialog.run_callable(
                QApplication.activeModalWidget(),
                lambda ldialog: self.scanner.import_installed_translations(
                    selected_mods, ldialog
                ),
            )

        ResultDialog(
            self.state_service.get_modfile_state_summary(
                [m for modfiles in selected_modfiles.values() for m in modfiles]
            ),
            QApplication.activeModalWidget(),
        ).exec()

    def online_scan(self) -> None:
        selected_modfiles: dict[Mod, list[ModFile]] = self.get_selected_modfiles()

        scan_result: dict[ModFile, TranslationStatus] = join_dicts(
            *LoadingDialog.run_callable(
                QApplication.activeModalWidget(),
                lambda ldialog: self.scanner.run_online_scan(
                    selected_modfiles, ldialog
                ),
            ).values()
        )
        self.state_service.set_modfile_states(scan_result)

        ResultDialog(
            self.state_service.get_modfile_state_summary(
                [m for modfiles in selected_modfiles.values() for m in modfiles]
            ),
            QApplication.activeModalWidget(),
        ).exec()

    def download_and_install_translations(self) -> None:
        download_entries: dict[tuple[str, ModId], list[TranslationDownload]] = (
            LoadingDialog.run_callable(
                QApplication.activeModalWidget(),
                lambda ldialog: self.download_manager.collect_available_downloads(
                    self.get_selected_modfiles(), ldialog
                ),
            )
        )

        DownloadListDialog(
            download_entries,
            self.provider,
            self.database,
            self.download_manager,
            self.nxm_listener,
            parent=QApplication.activeModalWidget(),
        ).exec()

    def build_output(self) -> None:
        output_path: Path = LoadingDialog.run_callable(
            QApplication.activeModalWidget(),
            lambda ldialog: self.database.exporter.build_output_mod(
                self.app_config.output_path or (get_current_path() / "SSE-AT Output"),
                self.mod_instance,
                self.app_config.get_tmp_dir(),
                ldialog,
            ),
        )

        message_box = QMessageBox()
        message_box.setWindowTitle(self.tr("Success!"))
        message_box.setText(self.tr("Created output mod at: ") + str(output_path))
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
        result: dict[ModFile, TranslationStatus] = LoadingDialog.run_callable(
            QApplication.activeModalWidget(), self.scanner.run_deep_scan
        )
        self.state_service.set_modfile_states(result)

        ResultDialog(
            self.state_service.get_modfile_state_summary(),
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

    def set_state_filter(self, state_filter: list[TranslationStatus]) -> None:
        """
        Sets the state filter.

        Args:
            state_filter (list[TranslationStatus]): The states to filter by.
        """

        self.__state_filter = state_filter
        self.__update()

    def __save_modfile_states(self) -> None:
        modfile_states: dict[Path, tuple[bool, TranslationStatus]] = {
            modfile.path: (item.checkState(0) == Qt.CheckState.Checked, modfile.status)
            for modfile_item in self.__modfile_items.values()
            for modfile, item in modfile_item.items()
        }

        self.cache.update_states_cache(modfile_states)
