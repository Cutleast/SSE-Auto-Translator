"""
Copyright (c) Cutleast
"""

import logging
import os
import webbrowser
from pathlib import Path
from typing import Optional

from cutleast_core_lib.core.utilities.filesystem import open_in_explorer
from cutleast_core_lib.ui.utilities.tree_widget import are_children_visible
from cutleast_core_lib.ui.widgets.loading_dialog import LoadingDialog
from PySide6.QtCore import Qt, Signal
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

from core.config.app_config import AppConfig
from core.database.database import TranslationDatabase
from core.database.database_service import DatabaseService
from core.database.importer import Importer
from core.database.translation import Translation
from core.mod_file.mod_file import ModFile
from core.mod_file.plugin_file import PluginFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.mod_instance.state_service import StateService
from core.plugin_interface import plugin as esp
from core.string import StringList
from core.string.string_status import StringStatus
from core.translation_provider.exceptions import ModNotFoundError
from core.translation_provider.provider import Provider
from core.translation_provider.source import Source
from core.user_data.user_data import UserData
from core.utilities import matches_filter
from ui.widgets.string_list.string_list_dialog import StringListDialog

from .help_dialog import ModInstanceHelpDialog
from .modinstance_menu import ModInstanceMenu


class ModInstanceWidget(QTreeWidget):
    """
    Widget for displaying the loaded modlist.
    """

    log: logging.Logger = logging.getLogger("ModInstance")

    basic_scan_requested = Signal()
    """Signal emitted when the user requests a basic scan via the context menu."""

    online_scan_requested = Signal()
    """Signal emitted when the user requests an online scan via the context menu."""

    downloads_requested = Signal()
    """Signal emitted when the user requests downloads via the context menu."""

    deep_scan_requested = Signal()
    """Signal emitted when the user requests a deep scan via the context menu."""

    highlight_translation_requested = Signal(Translation)
    """
    Signal emitted when the user requests to highlight a translation via the context
    menu.

    Args:
        Translation: Translation to highlight in the "Translations" panel.
    """

    edit_translation_requested = Signal(Translation)
    """
    Signal emitted when the user requests to edit a translation via the context menu.

    Args:
        Translation: Translation to open with the editor.
    """

    app_config: AppConfig
    user_data: UserData
    database: TranslationDatabase
    provider: Provider

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
        app_config: AppConfig,
        user_data: UserData,
        provider: Provider,
        state_service: StateService,
    ) -> None:
        super().__init__()

        self.app_config = app_config
        self.user_data = user_data
        self.database = user_data.database
        self.provider = provider
        self.mod_instance = user_data.modinstance
        self.state_service = state_service

        self.__init_ui()

        self.__menu.expand_all_clicked.connect(self.expandAll)
        self.__menu.collapse_all_clicked.connect(self.collapseAll)
        self.__menu.uncheck_selected_clicked.connect(self.__uncheck_selected)
        self.__menu.check_selected_clicked.connect(self.__check_selected)
        self.__menu.basic_scan_requested.connect(self.basic_scan_requested.emit)
        self.__menu.online_scan_requested.connect(self.online_scan_requested.emit)
        self.__menu.download_requested.connect(self.downloads_requested.emit)
        self.__menu.deep_scan_requested.connect(self.deep_scan_requested.emit)
        self.__menu.import_as_translation_requested.connect(
            self.__import_as_translation
        )
        self.__menu.show_untranslated_strings_requested.connect(
            self.__show_untranslated_strings
        )
        self.__menu.show_translation_requested.connect(self.__show_translation)
        self.__menu.show_translation_strings_requested.connect(
            self.__show_translation_strings
        )
        self.__menu.edit_translation_requested.connect(self.__edit_translation)
        self.__menu.create_translation_requested.connect(self.__create_translation)
        self.__menu.show_plugin_structure_requested.connect(
            self.__show_plugin_structure
        )
        self.__menu.add_to_ignore_list_requested.connect(self.__add_to_ignore_list)
        self.__menu.open_requested.connect(self.__open_modfile)
        self.__menu.show_strings_requested.connect(self.__show_strings)
        self.__menu.open_modpage_requested.connect(self.__open_modpage)
        self.__menu.open_in_explorer_requested.connect(self.__open_in_explorer)

        self.state_service.update_signal.connect(self.__update)

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
        self.__menu = ModInstanceMenu()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.__open_context_menu)

    def __open_context_menu(self) -> None:
        self.__menu.open(self.__get_current_item(), self.get_selected_items()[1])

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
            if mod.mod_type == Mod.Type.Separator:
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
                separator.name,
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
                str(modfile.path),
                "",  # Version
                "",  # Priority
            ]
        )
        modfile_item.setToolTip(0, str(modfile.full_path))
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
                ignored: bool = self.user_data.masterlist.is_ignored(modfile.name)
                item.setDisabled(ignored)
                if ignored:
                    item.setCheckState(0, Qt.CheckState.Unchecked)

                if self.app_config.debug_mode:
                    item.setToolTip(1, modfile.status.name)

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
                (
                    self.__state_filter is not None
                    and TranslationStatus.NoneStatus not in self.__state_filter
                    and not are_children_visible(mod_item)
                )
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

    def __show_strings(self) -> None:
        """
        Show the strings of the current item.
        """

        current_item: Optional[Mod | ModFile] = self.__get_current_item()

        if isinstance(current_item, ModFile):
            dialog = StringListDialog(current_item.name, current_item.get_strings())
            dialog.show()

        elif isinstance(current_item, Mod):
            strings: dict[Path, StringList] = {}

            for modfile in current_item.modfiles:
                modfile_strings = modfile.get_strings()
                strings[modfile.full_path.relative_to(current_item.path)] = (
                    modfile_strings
                )

            dialog = StringListDialog(current_item.name, strings)
            dialog.show()

    def __show_plugin_structure(self) -> None:
        # TODO: Overhaul this
        current_item: Optional[Mod | ModFile] = self.__get_current_item()

        if isinstance(current_item, PluginFile):
            plugin = esp.Plugin(current_item.full_path)

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

    def __check_selected(self) -> None:
        for item in self.selectedItems():
            if Qt.ItemFlag.ItemIsUserCheckable in item.flags() and not item.text(2):
                item.setCheckState(0, Qt.CheckState.Checked)

    def __uncheck_selected(self) -> None:
        for item in self.selectedItems():
            if Qt.ItemFlag.ItemIsUserCheckable in item.flags() and not item.text(2):
                item.setCheckState(0, Qt.CheckState.Unchecked)

    def __add_to_ignore_list(self) -> None:
        _, selected_modfiles = self.get_selected_items()

        for modfile in selected_modfiles:
            self.user_data.masterlist.add_to_ignore_list(modfile.name)

        self.user_data.user_config.save()
        self.__update()

    def __open_modpage(self) -> None:
        current_item: Optional[Mod | ModFile] = self.__get_current_item()

        if isinstance(current_item, Mod) and current_item.mod_id:
            try:
                url: Optional[str] = self.provider.get_modpage_url(
                    current_item.mod_id, source=Source.NexusMods
                )
                webbrowser.open(url)
            except ModNotFoundError:
                pass

    def __open_in_explorer(self) -> None:
        current_item: Optional[Mod | ModFile] = self.__get_current_item()

        if current_item is not None:
            open_in_explorer(
                current_item.path
                if isinstance(current_item, Mod)
                else current_item.full_path
            )

    def __show_untranslated_strings(self) -> None:
        current_item: Optional[Mod | ModFile] = self.__get_current_item()
        translation: Optional[Translation] = None

        if not isinstance(current_item, ModFile):
            return

        translation = self.database.get_translation_by_modfile_path(current_item.path)

        if translation is not None:
            untranslated_strings: StringList = [
                string
                for string in translation.strings[current_item.path]
                if string.status == StringStatus.TranslationRequired
                or string.status == StringStatus.TranslationIncomplete
            ]

            if untranslated_strings:
                dialog = StringListDialog(translation.name, untranslated_strings)
                dialog.show()

    def __show_translation_strings(self) -> None:
        current_item: Optional[Mod | ModFile] = self.__get_current_item()
        translation: Optional[Translation] = None

        if current_item is None:
            return

        if isinstance(current_item, ModFile):
            translation = self.database.get_translation_by_modfile_path(
                current_item.path
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

    def __show_translation(self) -> None:
        current_item: Optional[Mod | ModFile] = self.__get_current_item()
        translation: Optional[Translation] = None

        if current_item is None:
            return

        if isinstance(current_item, ModFile):
            translation = self.database.get_translation_by_modfile_path(
                current_item.path
            )
        else:
            translation = self.database.get_translation_by_mod(current_item)

        self.highlight_translation_requested.emit(translation)

    def __create_translation(self) -> None:
        current_item: Optional[Mod | ModFile] = self.__get_current_item()

        if current_item is None:
            return

        if isinstance(current_item, ModFile):

            def process(ldialog: LoadingDialog) -> Translation:
                ldialog.updateProgress(text1=self.tr("Creating translation..."))

                return DatabaseService.create_translation_for_modfile(
                    current_item, self.database
                )
        else:

            def process(ldialog: LoadingDialog) -> Translation:
                ldialog.updateProgress(text1=self.tr("Creating translation..."))

                return DatabaseService.create_translation_for_mod(
                    current_item, self.database
                )

        translation = LoadingDialog.run_callable(
            QApplication.activeModalWidget(), process
        )

        if isinstance(current_item, ModFile):
            current_item.status = TranslationStatus.TranslationIncomplete
        # TODO: Set status of all relevant mod files if current item is a mod

        self.highlight_translation_requested.emit(translation)
        self.edit_translation_requested.emit(translation)

    def __import_as_translation(self) -> None:
        current_item: Optional[Mod | ModFile] = self.__get_current_item()

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
                        modfile.full_path.relative_to(current_item.path),
                        ignore_mods=[current_item],
                        ignore_states=[
                            TranslationStatus.IsTranslated,
                            TranslationStatus.TranslationInstalled,
                        ],
                    )

                    if original_mod is not None:
                        break

                if original_mod is not None:
                    strings: dict[Path, StringList] = (
                        Importer.import_mod_as_translation(current_item, original_mod)
                    )
                    DatabaseService.create_translation_from_mod(
                        current_item, original_mod, strings, self.database
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

    def __edit_translation(self) -> None:
        current_item: Optional[Mod | ModFile] = self.__get_current_item()

        translation: Optional[Translation] = None
        if isinstance(current_item, ModFile):
            translation = self.database.get_translation_by_modfile_path(
                current_item.path
            )
        elif isinstance(current_item, Mod):
            translation = self.database.get_translation_by_mod(current_item)

        if translation is not None:
            self.edit_translation_requested.emit(translation)

    def __open_modfile(self) -> None:
        current_item: Optional[Mod | ModFile] = self.__get_current_item()

        if isinstance(current_item, ModFile):
            os.startfile(current_item.full_path)

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

    def __get_current_item(self) -> Optional[Mod | ModFile]:
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
        current_item: Optional[Mod | ModFile] = self.__get_current_item()

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
            self.__show_strings()
        else:
            item.setExpanded(not item.isExpanded())

    def show_help(self) -> None:
        """
        Displays help popup.
        """

        ModInstanceHelpDialog(QApplication.activeModalWidget()).exec()

    def set_name_filter(self, name_filter: str, case_sensitive: bool) -> None:
        """
        Sets the name filter.

        Args:
            name_filter (str): The name to filter by.
            case_sensitive (bool): Case sensitivity.
        """

        if name_filter.strip():
            self.__name_filter = (name_filter, case_sensitive)
        else:
            self.__name_filter = None
        self.__update()

    def set_state_filter(self, state_filter: list[TranslationStatus]) -> None:
        """
        Sets the state filter.

        Args:
            state_filter (list[TranslationStatus]): The states to filter by.
        """

        self.__state_filter = state_filter if state_filter else None
        self.__update()
