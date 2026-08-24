"""
Copyright (c) Cutleast
"""

import logging
import os
import webbrowser
from pathlib import Path
from typing import Optional, cast, override

from cutleast_core_lib.core.filesystem.utils import open_in_explorer
from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.core.utilities.filter import matches_filter
from cutleast_core_lib.core.utilities.typing_utils import not_none
from cutleast_core_lib.ui.progress.dialog import ProgressDialog
from cutleast_core_lib.ui.progress.display import ProgressDisplay
from cutleast_core_lib.ui.theme.manager import ThemeManager
from cutleast_core_lib.ui.utilities.column_config import CellValue, TreeItem
from cutleast_core_lib.ui.utilities.tree_widget import are_children_visible
from cutleast_core_lib.ui.utilities.window_manager import WindowManager
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QApplication, QMessageBox, QTreeWidget, QTreeWidgetItem

from core.config.app_config import AppConfig
from core.database.database import TranslationDatabase
from core.database.database_service import DatabaseService
from core.database.translation import Translation
from core.file_source.file_source_factory import FileSourceFactory
from core.file_types.file_type import FileType
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.mod_instance.state_service import StateService
from core.string.string_extractor import StringExtractor
from core.string.string_status import StringStatus
from core.string.types import StringList
from core.translation_provider.exceptions import ModNotFoundError
from core.translation_provider.provider import TranslationProvider
from core.translation_provider.source import Source
from core.user_data.user_data import UserData
from ui.string_list.string_list_window import StringListWindow

from .columns import ModInstanceColumns
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

    __app_config: AppConfig
    __user_data: UserData
    __database: TranslationDatabase
    __provider: TranslationProvider
    __mod_instance: ModInstance
    __state_service: StateService
    __mod_items: dict[Mod, TreeItem[Mod]]
    __modfile_items: dict[Mod, dict[ModFile, TreeItem[ModFile]]]

    __menu: ModInstanceMenu
    __name_filter: Optional[tuple[str, bool]] = None
    __state_filter: Optional[list[TranslationStatus]] = None
    __type_filter: Optional[list[FileType]] = None

    def __init__(
        self,
        app_config: AppConfig,
        user_data: UserData,
        provider: TranslationProvider,
        state_service: StateService,
    ) -> None:
        """
        Args:
            app_config (AppConfig): The application configuration.
            user_data (UserData): The user data.
            provider (TranslationProvider): The translation provider.
            state_service (StateService): The state service for managing mod file states.
        """

        super().__init__()

        self.__app_config = app_config
        self.__user_data = user_data
        self.__database = user_data.database
        self.__provider = provider
        self.__mod_instance = user_data.mod_instance
        self.__state_service = state_service

        self.__init_ui()

        self.customContextMenuRequested.connect(self.__open_context_menu)
        self.itemDoubleClicked.connect(self.__item_double_clicked)

        self.__menu.set_provider_features_enabled(self.__provider.is_available)
        self.__menu.set_modpage_enabled(
            self.__provider.is_source_available(Source.NexusMods)
        )

        self.__menu.expand_all_clicked.connect(self.expandAll)
        self.__menu.collapse_all_clicked.connect(self.collapseAll)
        self.__menu.uncheck_selected_clicked.connect(self.__uncheck_selected)
        self.__menu.check_selected_clicked.connect(self.__check_selected)
        self.__menu.basic_scan_requested.connect(self.basic_scan_requested.emit)
        self.__menu.online_scan_requested.connect(self.online_scan_requested.emit)
        self.__menu.download_requested.connect(self.downloads_requested.emit)
        self.__menu.import_as_translation_requested.connect(self.__import_as_translation)
        self.__menu.show_untranslated_strings_requested.connect(
            self.__show_untranslated_strings
        )
        self.__menu.show_translation_requested.connect(self.__show_translation)
        self.__menu.show_translation_strings_requested.connect(
            self.__show_translation_strings
        )
        self.__menu.edit_translation_requested.connect(self.__edit_translation)
        self.__menu.create_translation_requested.connect(self.__create_translation)
        self.__menu.add_to_ignore_list_requested.connect(self.__add_to_ignore_list)
        self.__menu.open_requested.connect(self.__open_modfile)
        self.__menu.show_strings_requested.connect(self.__show_strings)
        self.__menu.open_modpage_requested.connect(self.__open_modpage)
        self.__menu.open_in_explorer_requested.connect(self.__open_in_explorer)

        self.__state_service.update_signal.connect(self.update)

        ThemeManager.get().theme_changed.connect(lambda _: self.update())

        self.__load_mod_instance()

        # only sort after loading the mod instance to avoid performance issues
        self.setSortingEnabled(True)
        self.sortByColumn(ModInstanceColumns.Priority.index, Qt.SortOrder.AscendingOrder)
        self.header().setSortIndicatorClearable(True)

    def __init_ui(self) -> None:
        ModInstanceColumns.apply_to_tree_widget(self)

        self.setUniformRowHeights(True)
        self.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.setExpandsOnDoubleClick(False)

        self.__init_context_menu()

    def __init_context_menu(self) -> None:
        self.__menu = ModInstanceMenu()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def __open_context_menu(self) -> None:
        self.__menu.open(
            self.__get_current_item(), self.get_selected_items()[1], self.__database
        )

    def __load_mod_instance(self) -> None:
        """
        Displays the loaded modlist.
        """

        self.__mod_items = {}
        self.__modfile_items = {}
        self.clear()

        checkstates: dict[ModFile, bool] = self.__state_service.load_states_from_cache()

        cur_separator: Optional[TreeItem[Mod]] = None
        for i, mod in enumerate(self.__mod_instance.mods, start=1):
            if mod.mod_type == Mod.Type.Separator:
                cur_separator = TreeItem(mod, ModInstanceColumns)
                cur_separator.setValue(
                    column=ModInstanceColumns.Priority,
                    value=CellValue(display_text=str(i), sort_key=i),
                )

                self.__mod_items[mod] = cur_separator
                self.addTopLevelItem(cur_separator)
            elif mod.mod_type == Mod.Type.Regular:
                mod_item = TreeItem(mod, ModInstanceColumns)
                mod_item.setValue(
                    column=ModInstanceColumns.Priority,
                    value=CellValue(display_text=str(i), sort_key=i),
                )

                self.__mod_items[mod] = mod_item
                self.__modfile_items[mod] = {}
                for mod_file in mod.modfiles:
                    mod_file_item = TreeItem(
                        mod_file, ModInstanceColumns, checkable=True
                    )
                    mod_file_item.setChecked(checkstates.get(mod_file, True))

                    self.__modfile_items[mod][mod_file] = mod_file_item
                    mod_item.addChild(mod_file_item)

                if cur_separator is not None:
                    cur_separator.addChild(mod_item)
                else:
                    self.addTopLevelItem(mod_item)

        self.update()

    @override
    def update(self) -> None:  # type: ignore
        """
        Updates the displayed modlist.
        """

        name_filter: Optional[str] = (
            self.__name_filter[0] if self.__name_filter else None
        )
        case_sensitive: Optional[bool] = (
            self.__name_filter[1] if self.__name_filter else None
        )

        # temporarily disable sorting to avoid performance issues
        self.setSortingEnabled(False)

        for mod, mod_item in self.__mod_items.items():
            modfile_items: dict[ModFile, TreeItem[ModFile]] = self.__modfile_items.get(
                mod, {}
            )

            for modfile, item in modfile_items.items():
                ignored: bool = self.__user_data.masterlist.is_ignored(modfile.name)
                if ignored:
                    item.setChecked(False)

                item.setDisabled(ignored)
                item.setHidden(
                    (
                        self.__state_filter is not None
                        and modfile.status not in self.__state_filter
                    )
                    or (
                        self.__type_filter is not None
                        and not any(
                            isinstance(modfile, file_type.get_file_type_cls())
                            for file_type in self.__type_filter
                        )
                    )
                    or not matches_filter(
                        modfile.name, name_filter, case_sensitive or False
                    )
                )
                item.update()

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
            mod_item.update()

        self.setSortingEnabled(True)  # re-enable sorting after updating

    def __show_strings(self) -> None:
        """
        Show the strings of the current item.
        """

        current_item: Optional[Mod | ModFile] = self.__get_current_item()

        if isinstance(current_item, ModFile):
            WindowManager.get().show(
                StringListWindow(current_item.name, current_item.get_strings())
            )

        elif isinstance(current_item, Mod):
            strings: dict[Path, StringList] = {}

            for modfile in current_item.modfiles:
                modfile_strings = modfile.get_strings()
                strings[modfile.full_path.relative_to(current_item.path)] = (
                    modfile_strings
                )

            WindowManager.get().show(StringListWindow(current_item.name, strings))

    def __check_selected(self) -> None:
        for item in self.selectedItems():
            if (
                isinstance(item, TreeItem)
                and isinstance(item.item, ModFile)
                and not item.isDisabled()
            ):
                item.setChecked(True)

    def __uncheck_selected(self) -> None:
        for item in self.selectedItems():
            if (
                isinstance(item, TreeItem)
                and isinstance(item.item, ModFile)
                and not item.isDisabled()
            ):
                item.setChecked(False)

    def __add_to_ignore_list(self) -> None:
        _, selected_modfiles = self.get_selected_items()

        for modfile in selected_modfiles:
            self.__user_data.masterlist.add_to_ignore_list(modfile.name)

        self.__user_data.user_config.save()
        self.update()

    def __open_modpage(self) -> None:
        current_item: Optional[Mod | ModFile] = self.__get_current_item()

        if isinstance(current_item, Mod) and current_item.mod_id:
            try:
                url: Optional[str] = self.__provider.get_modpage_url(
                    current_item.mod_id, source=Source.NexusMods
                )
                webbrowser.open(url)
            except ModNotFoundError:
                pass

    def __open_in_explorer(self) -> None:
        current_item: Optional[Mod | ModFile] = self.__get_current_item()

        if current_item is not None:
            if (
                isinstance(current_item, ModFile)
                and not FileSourceFactory.for_file_path(
                    current_item.full_path
                ).is_real_file()
            ):
                # there is no real file to show in explorer
                return

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

        translation = self.__database.get_translation_by_modfile_path(current_item.path)

        if translation is not None:
            untranslated_strings: StringList = [
                string
                for string in translation.strings[current_item.path]
                if string.status == StringStatus.TranslationRequired
                or string.status == StringStatus.TranslationIncomplete
            ]

            if untranslated_strings:
                WindowManager.get().show(
                    StringListWindow(translation.name, untranslated_strings)
                )

    def __show_translation_strings(self) -> None:
        current_item: Optional[Mod | ModFile] = self.__get_current_item()
        translation: Optional[Translation] = None

        if current_item is None:
            return

        if isinstance(current_item, ModFile):
            translation = self.__database.get_translation_by_modfile_path(
                current_item.path
            )
        else:
            translation = self.__database.get_translation_by_mod(current_item)

        if translation is not None:
            WindowManager.get().show(
                StringListWindow(
                    translation.name,
                    translation.strings,
                    translation_mode=True,
                )
            )

    def __show_translation(self) -> None:
        current_item: Optional[Mod | ModFile] = self.__get_current_item()
        translation: Optional[Translation] = None

        if current_item is None:
            return

        if isinstance(current_item, ModFile):
            translation = self.__database.get_translation_by_modfile_path(
                current_item.path
            )
        else:
            translation = self.__database.get_translation_by_mod(current_item)

        if translation is not None:
            self.highlight_translation_requested.emit(translation)
        else:
            self.log.error(f"No translation found for {current_item}.")

    def __create_translation(self) -> None:
        current_item: Optional[Mod | ModFile] = self.__get_current_item()

        if current_item is None:
            return

        selected_mods: list[Mod] = [
            mod for mod, item in self.__mod_items.items() if item.isSelected()
        ]
        selected_modfiles: list[ModFile] = [
            modfile
            for modfile_items in self.__modfile_items.values()
            for modfile, item in modfile_items.items()
            if item.isSelected()
        ]

        def process(pdisplay: ProgressDisplay) -> None:
            pdisplay.updateMainProgress(
                ProgressUpdate(status_text=self.tr("Creating translations for mods..."))
            )

            t: int = 0
            translation: Translation
            modfile_states: dict[ModFile, TranslationStatus] = {}
            for m, selected_mod in enumerate(selected_mods):
                pdisplay.updateMainProgress(
                    ProgressUpdate(
                        status_text=(
                            self.tr("Creating translation for mod '{mod}'...").format(
                                mod=selected_mod.name
                            )
                            + f" ({m + 1}/{len(selected_mods)})"
                        ),
                        value=m,
                        maximum=len(selected_mods),
                    )
                )

                translation = DatabaseService.create_translation_for_mod(
                    selected_mod, self.__database
                )
                t += 1

                modfile_states.update(
                    {
                        not_none(
                            self.__mod_instance.get_modfile(path)
                        ): TranslationStatus.TranslationIncomplete
                        for path in translation.strings
                    }
                )

            for m, selected_modfile in enumerate(selected_modfiles):
                pdisplay.updateMainProgress(
                    ProgressUpdate(
                        status_text=(
                            self.tr(
                                "Creating translation for mod file '{modfile}'..."
                            ).format(modfile=selected_modfile.path)
                            + f" ({m + 1}/{len(selected_modfiles)})"
                        ),
                        value=m,
                        maximum=len(selected_modfiles),
                    )
                )

                if selected_modfile in modfile_states or selected_modfile.status in [
                    TranslationStatus.NoStrings,
                    TranslationStatus.TranslationInstalled,
                    TranslationStatus.IsTranslated,
                ]:
                    continue  # no translation required for the mod file

                translation = DatabaseService.create_translation_for_modfile(
                    selected_modfile, self.__database
                )
                t += 1

                modfile_states[selected_modfile] = (
                    TranslationStatus.TranslationIncomplete
                )

            self.__state_service.set_modfile_states(modfile_states)

            if t == 1:
                self.highlight_translation_requested.emit(translation)  # pyright: ignore[reportPossiblyUnboundVariable]
                self.edit_translation_requested.emit(translation)  # pyright: ignore[reportPossiblyUnboundVariable]

        ProgressDialog(process, QApplication.activeModalWidget()).run()

    def __import_as_translation(self) -> None:
        current_item: Optional[Mod | ModFile] = self.__get_current_item()

        if isinstance(current_item, Mod):

            def process(pdisplay: ProgressDisplay) -> None:
                pdisplay.updateMainProgress(
                    ProgressUpdate(
                        status_text=self.tr("Importing installed translation...")
                    )
                )

                # TODO: Make the import dependent on the original mod files instead of a single mod
                # Find the original mod
                original_mod: Optional[Mod] = None
                for modfile in current_item.modfiles:
                    original_mod = self.__mod_instance.get_mod_with_modfile(
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
                        StringExtractor.map_strings_from_mods(current_item, original_mod)
                    )
                    DatabaseService.create_translation_from_mod(
                        current_item, original_mod, strings, self.__database
                    )
                else:
                    raise FileNotFoundError(
                        f"Could not find original mod for '{current_item.name}'"
                    )

            ProgressDialog(process, QApplication.activeModalWidget()).run()

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
            translation = self.__database.get_translation_by_modfile_path(
                current_item.path
            )
        elif isinstance(current_item, Mod):
            translation = self.__database.get_translation_by_mod(current_item)

        if translation is not None:
            self.edit_translation_requested.emit(translation)

    def __open_modfile(self) -> None:
        current_item: Optional[Mod | ModFile] = self.__get_current_item()

        if isinstance(current_item, ModFile):
            os.startfile(
                FileSourceFactory.for_file_path(current_item.full_path).get_real_file()
            )

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

    def get_checked_items(self, filtered: bool = True) -> dict[Mod, list[ModFile]]:
        """
        Args:
            filtered (bool, optional):
                Whether to return only visible items. Defaults to True.

        Returns:
            dict[Mod, list[ModFile]]: All mod files whose items are checked.
        """

        return {
            mod: [
                modfile
                for modfile, item in modfile_items.items()
                if item.isChecked() and (not filtered or not item.isHidden())
            ]
            for mod, modfile_items in self.__modfile_items.items()
        }

    def __get_current_item(self) -> Optional[Mod | ModFile]:
        """
        Returns the item where the cursor is.

        Returns:
            Optional[Mod | ModFile]: Current item or None
        """

        current_item: Optional[QTreeWidgetItem] = self.currentItem()

        if not isinstance(current_item, TreeItem):
            return

        return cast(TreeItem[Mod | ModFile], current_item).item

    def __item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        current_item: Optional[Mod | ModFile] = self.__get_current_item()

        if (
            current_item is not None
            and not (
                isinstance(current_item, Mod)
                and current_item.mod_type == Mod.Type.Separator
            )
            and (
                not isinstance(current_item, Mod)
                or any(
                    modfile.status != TranslationStatus.NoStrings
                    for modfile in current_item.modfiles
                )
            )
        ) and self.__app_config.show_strings_on_double_click:
            self.__show_strings()
        else:
            item.setExpanded(not item.isExpanded())

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
        self.update()

    def set_state_filter(self, state_filter: list[TranslationStatus]) -> None:
        """
        Sets the state filter.

        Args:
            state_filter (list[TranslationStatus]): The states to filter by.
        """

        self.__state_filter = state_filter if state_filter else None
        self.update()

    def set_type_filter(self, type_filter: list[FileType]) -> None:
        """
        Sets the file type filter.

        Args:
            type_filter (list[FileType]): The file types to filter by.
        """

        self.__type_filter = type_filter if type_filter else None
        self.update()

    def get_visible_modfiles(self, only_checked: bool = True) -> list[ModFile]:
        """
        Args:
            only_checked (bool, optional):
                Only return items that are checked. Defaults to True.

        Returns:
            list[ModFile]: List of visible mod files with the current active filter.
        """

        return [
            modfile
            for modfile_items in self.__modfile_items.values()
            for modfile, modfile_item in modfile_items.items()
            if (
                not modfile_item.isHidden()
                and (not only_checked or modfile_item.isChecked())
            )
        ]

    def get_visible_modfile_item_count(self, only_checked: bool = True) -> int:
        """
        Args:
            only_checked (bool): Only count items that are checked.

        Returns:
            int: Number of visible modfile items with the current active filter
        """

        return len(self.get_visible_modfiles(only_checked))

    def is_modfile_checked(self, modfile: ModFile, mod: Mod) -> bool:
        """
        Checks if the item of a mod file is checked.

        Args:
            modfile (ModFile): Mod file.
            mod (Mod): Mod the file is belonging to.

        Returns:
            bool: Whether the item is checked.
        """

        return self.__modfile_items[mod][modfile].isChecked()
