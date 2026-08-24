"""
Copyright (c) Cutleast
"""

from collections.abc import Callable
from pathlib import Path
from typing import Optional, override

from cutleast_core_lib.core.utilities.typing_utils import not_none
from cutleast_core_lib.ui.widgets.tree_menu import TreeMenu
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction

from core.database.translation import Translation
from core.translation_provider.source import Source
from ui.utilities.icon_provider import IconProvider, ResourceIcon


class TranslationsMenu(TreeMenu):
    """
    Context menu for translations tab.
    """

    show_strings_requested = Signal()
    """Signal emitted when the user clicks on the show strings action."""

    edit_translation_requested = Signal()
    """Signal emitted when the user clicks on the edit translation action."""

    rename_translation_requested = Signal()
    """Signal emitted when the user clicks on the rename translation action."""

    export_translation_requested = Signal()
    """Signal emitted when the user clicks on the export translation action."""

    delete_translation_requested = Signal()
    """Signal emitted when the user clicks on the delete translation action."""

    open_modpage_requested = Signal()
    """Signal emitted when the user clicks on the open modpage action."""

    open_in_explorer_requested = Signal()
    """Signal emitted when the user clicks on the open in explorer action."""

    __show_strings_action: QAction
    __edit_translation_action: QAction
    __rename_translation_action: QAction
    __export_translation_action: QAction
    __delete_translation_action: QAction
    __open_modpage_action: QAction
    __open_in_explorer_action: QAction

    @override
    def __init__(self) -> None:
        super().__init__()

        self.__init_translation_actions()
        self.__init_open_actions()

        self.__show_strings_action.triggered.connect(self.show_strings_requested.emit)
        self.__edit_translation_action.triggered.connect(
            self.edit_translation_requested.emit
        )
        self.__rename_translation_action.triggered.connect(
            self.rename_translation_requested.emit
        )
        self.__export_translation_action.triggered.connect(
            self.export_translation_requested.emit
        )
        self.__delete_translation_action.triggered.connect(
            self.delete_translation_requested.emit
        )

    def __init_translation_actions(self) -> None:
        self.__show_strings_action = self.addAction(
            self.tr("Show translation strings...")
        )
        IconProvider.bind_qta_icon(
            self.__show_strings_action,
            self.__show_strings_action.setIcon,
            "mdi6.book-open-outline",
        )

        self.__edit_translation_action = self.addAction(self.tr("Edit translation..."))
        IconProvider.bind_qta_icon(
            self.__edit_translation_action,
            self.__edit_translation_action.setIcon,
            "mdi6.book-edit",
        )

        self.__rename_translation_action = self.addAction(
            self.tr("Rename translation...")
        )
        IconProvider.bind_qta_icon(
            self.__rename_translation_action,
            self.__rename_translation_action.setIcon,
            "mdi6.rename",
        )

        self.__export_translation_action = self.addAction(
            self.tr("Export translation...")
        )
        IconProvider.bind_qta_icon(
            self.__export_translation_action,
            self.__export_translation_action.setIcon,
            "mdi6.share",
        )

        self.__delete_translation_action = self.addAction(
            self.tr("Delete selected translation(s)...")
        )
        IconProvider.bind_qta_icon(
            self.__delete_translation_action,
            self.__delete_translation_action.setIcon,
            "mdi6.delete",
        )

        self.addSeparator()

    def __init_open_actions(self) -> None:
        self.__open_modpage_action = self.addAction(
            IconProvider.get_res_icon(ResourceIcon.NexusMods),
            self.tr("Open mod page..."),
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
        current_item: Optional[Translation | Path],
        is_source_available: Callable[[Source], bool],
    ) -> None:
        """
        Opens the context menu at the current cursor position.

        Args:
            current_item (Optional[Translation | Path]):
                The current item in the tree view.
            is_source_available (Callable[[Source], bool]): Checks source availability.
        """

        if (
            isinstance(current_item, Translation)
            and current_item.source != Source.Local
            and is_source_available(current_item.source)
        ):
            self.__open_modpage_action.setVisible(True)
            self.__open_modpage_action.setIcon(not_none(current_item.source.get_icon()))
        else:
            self.__open_modpage_action.setVisible(False)

        self.__show_strings_action.setVisible(isinstance(current_item, Translation))
        self.__edit_translation_action.setVisible(isinstance(current_item, Translation))
        self.__rename_translation_action.setVisible(
            isinstance(current_item, Translation)
        )
        self.__export_translation_action.setVisible(
            isinstance(current_item, Translation)
        )
        self.__delete_translation_action.setVisible(
            isinstance(current_item, Translation)
        )
        self.__open_in_explorer_action.setVisible(isinstance(current_item, Translation))

        super().open()
