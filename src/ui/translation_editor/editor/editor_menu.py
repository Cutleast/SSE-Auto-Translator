"""
Copyright (c) Cutleast
"""

from typing import override

import qtawesome as qta
from cutleast_core_lib.ui.widgets.tree_menu import TreeMenu
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QKeySequence

from core.string.string_status import StringStatus
from ui.utilities.icon_provider import IconProvider


class EditorMenu(TreeMenu):
    """
    Context menu for editor tab.
    """

    edit_string_requested = Signal()
    """Signal emitted when the user clicks on the edit string action."""

    copy_string_requested = Signal()
    """Signal emitted when the user clicks on the copy string action."""

    reset_translation_requested = Signal()
    """Signal emitted when the user clicks on the reset translation action."""

    mark_as_requested = Signal(StringStatus)
    """
    Signal emitted when the user clicks on a mark as action.

    Args:
        Status: The string status to set.
    """

    __edit_string_action: QAction
    __copy_string_action: QAction
    __reset_string_action: QAction
    __mark_as_actions: dict[StringStatus, QAction]

    @override
    def __init__(self) -> None:
        super().__init__()

        self.__init_actions()
        self.__init_mark_actions()

    def __init_actions(self) -> None:
        self.__edit_string_action = self.addAction(
            IconProvider.get_qta_icon("mdi6.rename"), self.tr("Edit string...")
        )
        self.__edit_string_action.triggered.connect(self.edit_string_requested.emit)

        self.__copy_string_action = self.addAction(
            IconProvider.get_qta_icon("mdi6.content-copy"), self.tr("Copy string")
        )
        self.__copy_string_action.setIconVisibleInMenu(True)
        self.__copy_string_action.triggered.connect(self.copy_string_requested.emit)

        self.__reset_string_action = self.addAction(
            IconProvider.get_qta_icon("ri.arrow-go-back-line"),
            self.tr("Reset selected string(s)"),
        )
        self.__reset_string_action.setShortcut(QKeySequence("F4"))
        self.__reset_string_action.triggered.connect(
            self.reset_translation_requested.emit
        )

        self.addSeparator()

    def __init_mark_actions(self) -> None:
        status_shortcuts: dict[StringStatus, QKeySequence] = {
            StringStatus.TranslationComplete: QKeySequence("F1"),
            StringStatus.TranslationIncomplete: QKeySequence("F2"),
            StringStatus.NoTranslationRequired: QKeySequence("F3"),
        }

        self.__mark_as_actions = {}
        for status in StringStatus:
            # Skip NoneStatus
            if status == StringStatus.NoneStatus:
                continue

            mark_as_action: QAction = self.addAction(
                qta.icon(
                    "mdi6.square-rounded",
                    color=StringStatus.get_color(status),
                ),
                self.tr('Mark as "{0}"').format(status.get_localized_name()),
            )
            if status in status_shortcuts:
                mark_as_action.setShortcut(status_shortcuts[status])

            mark_as_action.triggered.connect(
                lambda _, s=status: self.mark_as_requested.emit(s)
            )

            self.__mark_as_actions[status] = mark_as_action

        self.addSeparator()

    @override
    def open(self, strings_selected: bool) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Opens the menu at the current mouse cursor position.

        Args:
            strings_selected (bool): Whether any strings are selected.
        """

        self.__edit_string_action.setVisible(strings_selected)
        self.__copy_string_action.setVisible(strings_selected)
        self.__reset_string_action.setVisible(strings_selected)
        for action in self.__mark_as_actions.values():
            action.setVisible(strings_selected)

        super().open()
