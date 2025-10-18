"""
Copyright (c) Cutleast
"""

import qtawesome as qta
from cutleast_core_lib.ui.widgets.menu import Menu
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QCursor, QKeySequence

from core.string.string_status import StringStatus
from ui.utilities.icon_provider import IconProvider


class EditorMenu(Menu):
    """
    Context menu for editor tab.
    """

    expand_all_clicked = Signal()
    """Signal emitted when the user clicks on the expand all action."""

    collapse_all_clicked = Signal()
    """Signal emitted when the user clicks on the collapse all action."""

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

    def __init__(self) -> None:
        super().__init__()

        self.__init_separator_actions()
        self.__init_actions()
        self.__init_mark_actions()

    def __init_separator_actions(self) -> None:
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

        self.addSeparator()

    def __init_actions(self) -> None:
        edit_string_action: QAction = self.addAction(
            IconProvider.get_qta_icon("mdi6.rename"), self.tr("Edit string...")
        )
        edit_string_action.triggered.connect(self.edit_string_requested.emit)

        copy_action: QAction = self.addAction(
            IconProvider.get_qta_icon("mdi6.content-copy"), self.tr("Copy string")
        )
        copy_action.setIconVisibleInMenu(True)
        copy_action.triggered.connect(self.copy_string_requested.emit)

        reset_string_action: QAction = self.addAction(
            IconProvider.get_qta_icon("ri.arrow-go-back-line"),
            self.tr("Reset selected string(s)"),
        )
        reset_string_action.setShortcut(QKeySequence("F4"))
        reset_string_action.triggered.connect(self.reset_translation_requested.emit)

        self.addSeparator()

    def __init_mark_actions(self) -> None:
        status_shortcuts: dict[StringStatus, QKeySequence] = {
            StringStatus.TranslationComplete: QKeySequence("F1"),
            StringStatus.TranslationIncomplete: QKeySequence("F2"),
            StringStatus.NoTranslationRequired: QKeySequence("F3"),
        }

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

        self.addSeparator()

    def open(self) -> None:
        self.exec(QCursor.pos())
