"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from cutleast_core_lib.ui.widgets.menu import Menu
from cutleast_core_lib.ui.widgets.tree_menu import TreeMenu
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction

from core.database.database import TranslationDatabase
from core.file_source.file_source_factory import FileSourceFactory
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from ui.utilities.icon_provider import IconProvider, ResourceIcon


class ModInstanceMenu(TreeMenu):
    """
    Context menu for mod instance widget.
    """

    uncheck_selected_clicked = Signal()
    """Signal emitted when the user clicks on the uncheck selected action."""

    check_selected_clicked = Signal()
    """Signal emitted when the user clicks on the check selected action."""

    basic_scan_requested = Signal()
    """Signal emitted when the user clicks on the basic scan action."""

    online_scan_requested = Signal()
    """Signal emitted when the user clicks on the online scan action."""

    download_requested = Signal()
    """Signal emitted when the user clicks on the download action."""

    import_as_translation_requested = Signal()
    """Signal emitted when the user clicks on the import as translation action."""

    show_untranslated_strings_requested = Signal()
    """Signal emitted when the user clicks on the show untranslated strings action."""

    show_translation_requested = Signal()
    """Signal emitted when the user clicks on the show translation action."""

    show_translation_strings_requested = Signal()
    """Signal emitted when the user clicks on the show translation strings action."""

    edit_translation_requested = Signal()
    """Signal emitted when the user clicks on the edit translation action."""

    create_translation_requested = Signal()
    """Signal emitted when the user clicks on the create translation action."""

    add_to_ignore_list_requested = Signal()
    """Signal emitted when the user clicks on the add to ignore list action."""

    open_requested = Signal()
    """Signal emitted when the user clicks on the open action."""

    show_strings_requested = Signal()
    """Signal emitted when the user clicks on the show strings action."""

    open_modpage_requested = Signal()
    """Signal emitted when the user clicks on the open mod page action."""

    open_in_explorer_requested = Signal()
    """Signal emitted when the user clicks on the open in explorer action."""

    __action_menu: Menu
    """
    Submenu for scan and download actions.
    """

    __translation_menu: Menu
    """
    Submenu for translation-related actions.
    """

    __modfile_menu: Menu
    """
    Submenu for mod file-related actions.
    """

    # General actions
    __uncheck_action: QAction
    __check_action: QAction
    __show_strings_action: QAction
    __online_scan_action: QAction
    __download_action: QAction

    # Translation-related actions
    # Installed translations
    __show_untranslated_strings_action: QAction
    __show_translation_action: QAction
    __show_translation_strings_action: QAction
    __edit_translation_action: QAction

    # New translations
    __create_translation_action: QAction
    __import_as_translation_action: QAction

    # "Open" actions
    __open_modpage_action: QAction
    __open_in_explorer_action: QAction

    @override
    def __init__(self) -> None:
        super().__init__()

        self.__init_item_actions()
        self.__init_actions_menu()
        self.__init_translation_actions()
        self.__init_modfile_actions()
        self.__init_general_actions()

    def __init_item_actions(self) -> None:
        self.__uncheck_action = self.addAction(self.tr("Uncheck selected mod file(s)"))
        IconProvider.bind_qta_icon(
            self.__uncheck_action, self.__uncheck_action.setIcon, "mdi6.close"
        )
        self.__uncheck_action.triggered.connect(self.uncheck_selected_clicked.emit)

        self.__check_action = self.addAction(self.tr("Check selected mod file(s)"))
        IconProvider.bind_qta_icon(
            self.__check_action, self.__check_action.setIcon, "mdi6.check"
        )
        self.__check_action.triggered.connect(self.check_selected_clicked.emit)

        self.addSeparator()

    def __init_actions_menu(self) -> None:
        self.__action_menu = Menu(title=self.tr("Actions"))
        IconProvider.bind_qta_icon(
            self.__action_menu, self.__action_menu.setIcon, "mdi6.lightning-bolt"
        )
        self.addMenu(self.__action_menu)

        basic_scan_action: QAction = self.__action_menu.addAction(
            self.tr("Basic scan...")
        )
        IconProvider.bind_res_icon(
            basic_scan_action,
            basic_scan_action.setIcon,
            ResourceIcon.DetectLang,
        )
        basic_scan_action.triggered.connect(self.basic_scan_requested.emit)

        self.__online_scan_action = self.__action_menu.addAction(
            self.tr("Online scan...")
        )
        IconProvider.bind_res_icon(
            self.__online_scan_action,
            self.__online_scan_action.setIcon,
            ResourceIcon.ScanOnline,
        )
        self.__online_scan_action.triggered.connect(self.online_scan_requested.emit)

        self.__download_action = self.__action_menu.addAction(
            self.tr("Download available translations...")
        )
        IconProvider.bind_qta_icon(
            self.__download_action,
            self.__download_action.setIcon,
            "mdi6.download-multiple",
        )
        self.__download_action.triggered.connect(self.download_requested.emit)

    def __init_translation_actions(self) -> None:
        self.__translation_menu = Menu(title=self.tr("Translation"))
        IconProvider.bind_qta_icon(
            self.__translation_menu, self.__translation_menu.setIcon, "mdi6.translate"
        )
        self.addMenu(self.__translation_menu)

        self.__show_untranslated_strings_action = self.__translation_menu.addAction(
            self.tr("Show untranslated strings...")
        )
        IconProvider.bind_qta_icon(
            self.__show_untranslated_strings_action,
            self.__show_untranslated_strings_action.setIcon,
            "mdi6.book-alert-outline",
        )
        self.__show_untranslated_strings_action.triggered.connect(
            self.show_untranslated_strings_requested.emit
        )

        self.__show_translation_action = self.__translation_menu.addAction(
            self.tr("Show translation...")
        )
        IconProvider.bind_qta_icon(
            self.__show_translation_action,
            self.__show_translation_action.setIcon,
            "mdi6.translate",
        )
        self.__show_translation_action.triggered.connect(
            self.show_translation_requested.emit
        )

        self.__show_translation_strings_action = self.__translation_menu.addAction(
            self.tr("Show translation strings...")
        )
        IconProvider.bind_qta_icon(
            self.__show_translation_strings_action,
            self.__show_translation_strings_action.setIcon,
            "mdi6.book-open-outline",
        )
        self.__show_translation_strings_action.triggered.connect(
            self.show_translation_strings_requested.emit
        )

        self.__edit_translation_action = self.__translation_menu.addAction(
            self.tr("Edit translation...")
        )
        IconProvider.bind_qta_icon(
            self.__edit_translation_action,
            self.__edit_translation_action.setIcon,
            "mdi6.text-box-edit",
        )
        self.__edit_translation_action.triggered.connect(
            self.edit_translation_requested.emit
        )

        self.__translation_menu.addSeparator()

        self.__create_translation_action = self.__translation_menu.addAction(
            self.tr("Create new translation...")
        )
        IconProvider.bind_qta_icon(
            self.__create_translation_action,
            self.__create_translation_action.setIcon,
            "mdi6.passport-plus",
        )
        self.__create_translation_action.triggered.connect(
            self.create_translation_requested.emit
        )

        self.__import_as_translation_action = self.__translation_menu.addAction(
            self.tr("Import as translation...")
        )
        IconProvider.bind_qta_icon(
            self.__import_as_translation_action,
            self.__import_as_translation_action.setIcon,
            "mdi6.database-import-outline",
        )
        self.__import_as_translation_action.triggered.connect(
            self.import_as_translation_requested.emit
        )

        self.addSeparator()

    def __init_modfile_actions(self) -> None:
        self.__modfile_menu = Menu(title=self.tr("Mod files"))
        IconProvider.bind_res_icon(
            self.__modfile_menu,
            self.__modfile_menu.setIcon,
            ResourceIcon.Plugin,
        )
        self.addMenu(self.__modfile_menu)

        add_to_ignore_list_action: QAction = self.__modfile_menu.addAction(
            self.tr("Add mod file to ignore list")
        )
        IconProvider.bind_qta_icon(
            add_to_ignore_list_action,
            add_to_ignore_list_action.setIcon,
            "mdi6.playlist-remove",
        )
        add_to_ignore_list_action.triggered.connect(
            self.add_to_ignore_list_requested.emit
        )

        open_action = self.__modfile_menu.addAction(self.tr("Open..."))
        IconProvider.bind_qta_icon(open_action, open_action.setIcon, "mdi6.open-in-new")
        open_action.triggered.connect(self.open_requested.emit)

        self.addSeparator()

    def __init_general_actions(self) -> None:
        self.__show_strings_action = self.addAction(self.tr("Show strings..."))
        IconProvider.bind_qta_icon(
            self.__show_strings_action,
            self.__show_strings_action.setIcon,
            "mdi6.book-open-outline",
        )
        self.__show_strings_action.triggered.connect(self.show_strings_requested.emit)

        self.__open_modpage_action = self.addAction(
            IconProvider.get_res_icon(ResourceIcon.NexusMods),
            self.tr("Open mod page on Nexus Mods..."),
        )
        self.__open_modpage_action.triggered.connect(self.open_modpage_requested.emit)

        self.__open_in_explorer_action = self.addAction(self.tr("Open in Explorer..."))
        IconProvider.bind_qta_icon(
            self.__open_in_explorer_action,
            self.__open_in_explorer_action.setIcon,
            "mdi6.folder",
        )
        self.__open_in_explorer_action.triggered.connect(
            self.open_in_explorer_requested.emit
        )

    @override
    def open(
        self,
        current_item: Optional[Mod | ModFile],
        selected_modfiles: list[ModFile],
        database: TranslationDatabase,
    ) -> None:
        """
        Opens the context menu at the current cursor position.

        Args:
            current_item (Optional[Mod | ModFile]): The current item in the tree view.
            selected_modfiles (list[ModFile]): The selected mod files in the tree view.
            database (TranslationDatabase):
                The database containing the installed translations.
        """

        # check actions only visible if at least one mod file is selected
        self.__uncheck_action.setVisible(len(selected_modfiles) > 0)
        self.__check_action.setVisible(len(selected_modfiles) > 0)

        # actions only visible if at least one mod file is selected
        self.__action_menu.menuAction().setVisible(len(selected_modfiles) > 0)

        translation_installed: bool = (
            ModInstanceMenu.__is_translation_installed(current_item)
            if current_item is not None
            else False
        )

        # translation-related actions only visible if a translation is installed
        self.__show_untranslated_strings_action.setVisible(
            translation_installed and isinstance(current_item, ModFile)
        )
        self.__show_translation_action.setVisible(translation_installed)
        self.__show_translation_strings_action.setVisible(translation_installed)
        self.__edit_translation_action.setVisible(translation_installed)

        # import action only visible if current item is a mod with at
        # least one translated mod file and no translation is installed
        self.__import_as_translation_action.setVisible(
            (
                (
                    isinstance(current_item, ModFile)
                    and current_item.status == TranslationStatus.IsTranslated
                    and not database.get_translation_by_modfile_path(current_item.path)
                )
                or (
                    isinstance(current_item, Mod)
                    and any(
                        modfile.status == TranslationStatus.IsTranslated
                        and not database.get_translation_by_modfile_path(modfile.path)
                        for modfile in current_item.modfiles
                    )
                )
            )
            and not translation_installed
        )

        # create action only visible if no translation is installed but required
        self.__create_translation_action.setVisible(
            current_item is not None
            and not translation_installed
            and ModInstanceMenu.__is_translation_required(current_item)
        )

        # translation menu only visible if one of its actions is visible
        self.__translation_menu.menuAction().setVisible(
            self.__show_untranslated_strings_action.isVisible()
            or self.__show_translation_action.isVisible()
            or self.__show_translation_strings_action.isVisible()
            or self.__edit_translation_action.isVisible()
            or self.__import_as_translation_action.isVisible()
            or self.__create_translation_action.isVisible()
        )

        # mod file-related actions only visible if the current item is a mod file
        self.__modfile_menu.menuAction().setVisible(isinstance(current_item, ModFile))

        # show strings action only visible if the current item has strings
        self.__show_strings_action.setVisible(
            isinstance(current_item, ModFile)
            or (
                isinstance(current_item, Mod)
                and any(
                    modfile.status != TranslationStatus.NoStrings
                    for modfile in current_item.modfiles
                )
            )
        )

        # open in explorer action only visible if the current item is a mod file
        self.__open_in_explorer_action.setVisible(
            current_item is not None
            and not (
                isinstance(current_item, ModFile)
                and not FileSourceFactory.for_file_path(
                    current_item.full_path
                ).is_real_file()
            )
        )

        # open mod page action only visible if the current item is a mod and has a mod id
        self.__open_modpage_action.setVisible(
            isinstance(current_item, Mod) and current_item.mod_id is not None
        )

        super().open()

    def set_provider_features_enabled(self, enabled: bool) -> None:
        """
        Enables or disables actions that require a translation provider.

        Args:
            enabled (bool): Whether a translation provider is available.
        """

        self.__online_scan_action.setEnabled(enabled)
        self.__download_action.setEnabled(enabled)

    def set_modpage_enabled(self, enabled: bool) -> None:
        """
        Enables or disables the Nexus Mods modpage action.

        Args:
            enabled (bool): Whether the Nexus Mods provider is available.
        """

        self.__open_modpage_action.setEnabled(enabled)

    @staticmethod
    def __is_translation_installed(item: Mod | ModFile) -> bool:
        """
        Checks if a translation for a mod file or a mod is installed.

        Args:
            item (Mod | ModFile): The item to check.

        Returns:
            bool: Whether a translation is installed.
        """

        valid_states: list[TranslationStatus] = [
            TranslationStatus.TranslationInstalled,
            TranslationStatus.TranslationIncomplete,
        ]

        if isinstance(item, ModFile):
            return item.status in valid_states

        return any(modfile.status in valid_states for modfile in item.modfiles)

    @staticmethod
    def __is_translation_required(item: Mod | ModFile) -> bool:
        """
        Checks if a translation for a mod file or a mod is required.

        Args:
            item (Mod | ModFile): The item to check.

        Returns:
            bool: Whether a translation is required.
        """

        valid_states: list[TranslationStatus] = [
            TranslationStatus.RequiresTranslation,
            TranslationStatus.NoTranslationAvailable,
            TranslationStatus.TranslationAvailableInDatabase,
            TranslationStatus.TranslationAvailableOnline,
        ]

        if isinstance(item, ModFile):
            return item.status in valid_states

        return any(modfile.status in valid_states for modfile in item.modfiles)
