"""
Copyright (c) Cutleast
"""

from typing import Optional

from cutleast_core_lib.ui.widgets.menu import Menu
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QCursor

from core.file_source.file_source import FileSource
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from ui.utilities.icon_provider import IconProvider, ResourceIcon


class ModInstanceMenu(Menu):
    """
    Context menu for mod instance widget.
    """

    expand_all_clicked = Signal()
    """Signal emitted when the user clicks on the expand all action."""

    collapse_all_clicked = Signal()
    """Signal emitted when the user clicks on the collapse all action."""

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

    deep_scan_requested = Signal()
    """Signal emitted when the user clicks on the deep scan action."""

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

    __uncheck_action: QAction
    __check_action: QAction
    __show_strings_action: QAction
    __import_as_translation_action: QAction
    __open_modpage_action: QAction
    __open_in_explorer_action: QAction

    def __init__(self) -> None:
        super().__init__()

        self.__init_item_actions()
        self.__init_actions_menu()
        self.__init_translation_actions()
        self.__init_modfile_actions()
        self.__init_general_actions()

    def __init_item_actions(self) -> None:
        expand_all_action: QAction = self.addAction(
            IconProvider.get_qta_icon("mdi6.arrow-expand-vertical"),
            self.tr("Expand all"),
        )
        expand_all_action.triggered.connect(self.expand_all_clicked.emit)

        collapse_all_action: QAction = self.addAction(
            IconProvider.get_qta_icon("mdi6.arrow-collapse-vertical"),
            self.tr("Collapse all"),
        )
        collapse_all_action.triggered.connect(self.collapse_all_clicked.emit)

        self.__uncheck_action = self.addAction(self.tr("Uncheck selected mod file(s)"))
        self.__uncheck_action.setIcon(IconProvider.get_qta_icon("mdi6.close"))
        self.__uncheck_action.triggered.connect(self.uncheck_selected_clicked.emit)

        self.__check_action = self.addAction(self.tr("Check selected mod file(s)"))
        self.__check_action.setIcon(IconProvider.get_qta_icon("mdi6.check"))
        self.__check_action.triggered.connect(self.check_selected_clicked.emit)

        self.addSeparator()

    def __init_actions_menu(self) -> None:
        self.__action_menu = Menu(
            IconProvider.get_qta_icon("mdi6.lightning-bolt"), self.tr("Actions")
        )
        self.addMenu(self.__action_menu)

        basic_scan_action: QAction = self.__action_menu.addAction(
            IconProvider.get_res_icon(ResourceIcon.DetectLang), self.tr("Basic scan...")
        )
        basic_scan_action.triggered.connect(self.basic_scan_requested.emit)

        online_scan_action: QAction = self.__action_menu.addAction(
            IconProvider.get_res_icon(ResourceIcon.ScanOnline),
            self.tr("Online scan..."),
        )
        online_scan_action.triggered.connect(self.online_scan_requested.emit)

        download_action: QAction = self.__action_menu.addAction(
            IconProvider.get_qta_icon("mdi6.download-multiple"),
            self.tr("Download available translations..."),
        )
        download_action.triggered.connect(self.download_requested.emit)

        deep_scan_action: QAction = self.__action_menu.addAction(
            IconProvider.get_qta_icon("mdi6.line-scan"), self.tr("Deep scan...")
        )
        deep_scan_action.triggered.connect(self.deep_scan_requested.emit)

        self.__action_menu.addSeparator()

        self.__import_as_translation_action = self.__action_menu.addAction(
            IconProvider.get_qta_icon("mdi6.database-import-outline"),
            self.tr("Import as translation..."),
        )
        self.__import_as_translation_action.triggered.connect(
            self.import_as_translation_requested.emit
        )

    def __init_translation_actions(self) -> None:
        self.__translation_menu = Menu(
            IconProvider.get_qta_icon("mdi6.translate"), self.tr("Translation")
        )
        self.addMenu(self.__translation_menu)

        show_untranslated_strings_action: QAction = self.__translation_menu.addAction(
            IconProvider.get_qta_icon("mdi6.book-alert-outline"),
            self.tr("Show untranslated strings..."),
        )
        show_untranslated_strings_action.triggered.connect(
            self.show_untranslated_strings_requested.emit
        )

        show_translation_action: QAction = self.__translation_menu.addAction(
            IconProvider.get_qta_icon("mdi6.translate"), self.tr("Show translation...")
        )
        show_translation_action.triggered.connect(self.show_translation_requested.emit)

        show_translation_strings_action: QAction = self.__translation_menu.addAction(
            IconProvider.get_qta_icon("mdi6.book-open-outline"),
            self.tr("Show translation strings..."),
        )
        show_translation_strings_action.triggered.connect(
            self.show_translation_strings_requested.emit
        )

        edit_translation_action: QAction = self.__translation_menu.addAction(
            IconProvider.get_qta_icon("mdi6.text-box-edit"),
            self.tr("Edit translation..."),
        )
        edit_translation_action.triggered.connect(self.edit_translation_requested.emit)

        self.addSeparator()

    def __init_modfile_actions(self) -> None:
        self.__modfile_menu = Menu(
            IconProvider.get_res_icon(ResourceIcon.Plugin), self.tr("Mod files")
        )
        self.addMenu(self.__modfile_menu)

        create_translation_action: QAction = self.__modfile_menu.addAction(
            IconProvider.get_qta_icon("mdi6.passport-plus"),
            self.tr("Create new translation..."),
        )
        create_translation_action.triggered.connect(
            self.create_translation_requested.emit
        )

        add_to_ignore_list_action: QAction = self.__modfile_menu.addAction(
            IconProvider.get_qta_icon("mdi.playlist-remove"),
            self.tr("Add mod file to ignore list"),
        )
        add_to_ignore_list_action.triggered.connect(
            self.add_to_ignore_list_requested.emit
        )

        open_action = self.__modfile_menu.addAction(
            IconProvider.get_qta_icon("fa5s.external-link-alt"), self.tr("Open...")
        )
        open_action.triggered.connect(self.open_requested.emit)

        self.addSeparator()

    def __init_general_actions(self) -> None:
        self.__show_strings_action = self.addAction(
            IconProvider.get_qta_icon("mdi6.book-open-outline"),
            self.tr("Show strings..."),
        )
        self.__show_strings_action.triggered.connect(self.show_strings_requested.emit)

        self.__open_modpage_action = self.addAction(
            IconProvider.get_res_icon(ResourceIcon.NexusMods),
            self.tr("Open mod page on Nexus Mods..."),
        )
        self.__open_modpage_action.triggered.connect(self.open_modpage_requested.emit)

        self.__open_in_explorer_action = self.addAction(
            IconProvider.get_qta_icon("fa5s.folder"), self.tr("Open in Explorer...")
        )
        self.__open_in_explorer_action.triggered.connect(
            self.open_in_explorer_requested.emit
        )

    def open(
        self, current_item: Optional[Mod | ModFile], selected_modfiles: list[ModFile]
    ) -> None:
        """
        Opens the context menu at the current cursor position.

        Args:
            current_item (Optional[Mod | ModFile]): The current item in the tree view.
            selected_modfiles (list[ModFile]): The selected mod files in the tree view.
        """

        self.__uncheck_action.setVisible(len(selected_modfiles) > 0)
        self.__check_action.setVisible(len(selected_modfiles) > 0)

        self.__action_menu.menuAction().setVisible(isinstance(current_item, Mod))
        self.__import_as_translation_action.setVisible(
            isinstance(current_item, Mod)
            and any(
                modfile.status == TranslationStatus.IsTranslated
                for modfile in current_item.modfiles
            )
        )
        self.__modfile_menu.menuAction().setVisible(isinstance(current_item, ModFile))
        self.__translation_menu.menuAction().setVisible(
            isinstance(current_item, ModFile)
            and current_item.status
            in [
                TranslationStatus.TranslationInstalled,
                TranslationStatus.TranslationIncomplete,
            ]
        )

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

        self.__open_in_explorer_action.setVisible(
            current_item is not None
            and not (
                isinstance(current_item, ModFile)
                and not FileSource.from_file(current_item.full_path).is_real_file()
            )
        )
        self.__open_modpage_action.setVisible(
            isinstance(current_item, Mod) and current_item.mod_id is not None
        )

        self.exec(QCursor.pos())
