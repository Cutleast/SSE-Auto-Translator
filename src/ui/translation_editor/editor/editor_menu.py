"""
Copyright (c) Cutleast
"""

from typing import override

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

        self.__edit_string_action.triggered.connect(self.edit_string_requested.emit)
        self.__copy_string_action.triggered.connect(self.copy_string_requested.emit)
        self.__reset_string_action.triggered.connect(
            self.reset_translation_requested.emit
        )

    def __init_actions(self) -> None:
        self.__edit_string_action = self.addAction(self.tr("Edit string..."))
        IconProvider.bind_qta_icon(
            self.__edit_string_action, self.__edit_string_action.setIcon, "mdi6.rename"
        )

        self.__copy_string_action = self.addAction(self.tr("Copy string"))
        IconProvider.bind_qta_icon(
            self.__copy_string_action,
            self.__copy_string_action.setIcon,
            "mdi6.content-copy",
        )
        self.__copy_string_action.setIconVisibleInMenu(True)

        self.__reset_string_action = self.addAction(self.tr("Reset selected string(s)"))
        IconProvider.bind_qta_icon(
            self.__reset_string_action, self.__reset_string_action.setIcon, "mdi6.undo"
        )
        self.__reset_string_action.setShortcut(QKeySequence("F4"))

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
                self.tr('Mark as "{0}"').format(status.get_localized_name()),
            )
            IconProvider.bind_custom_icon(
                mark_as_action,
                mark_as_action.setIcon,
                lambda s=status: IconProvider.get_qta_icon(
                    "mdi6.square-rounded",
                    color=s.get_base_color().name(),
                    color_active=s.get_base_color().name(),
                ),
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
