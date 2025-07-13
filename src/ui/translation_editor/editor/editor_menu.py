"""
Copyright (c) Cutleast
"""

import qtawesome as qta
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QCursor, QKeySequence

from core.database.string import String
from ui.widgets.menu import Menu


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

    mark_as_requested = Signal(String.Status)
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
            qta.icon("mdi6.arrow-expand-vertical", color=self.palette().text().color()),
            self.tr("Expand all"),
        )
        expand_all_action.triggered.connect(self.expand_all_clicked.emit)

        collapse_all_action: QAction = self.addAction(
            qta.icon(
                "mdi6.arrow-collapse-vertical", color=self.palette().text().color()
            ),
            self.tr("Collapse all"),
        )
        collapse_all_action.triggered.connect(self.collapse_all_clicked.emit)

        self.addSeparator()

    def __init_actions(self) -> None:
        edit_string_action: QAction = self.addAction(
            qta.icon("mdi6.rename", color="#ffffff"), self.tr("Edit String...")
        )
        edit_string_action.triggered.connect(self.edit_string_requested.emit)

        copy_action: QAction = self.addAction(
            qta.icon("mdi6.content-copy", color="#ffffff"), self.tr("Copy String")
        )
        copy_action.setIconVisibleInMenu(True)
        copy_action.triggered.connect(self.copy_string_requested.emit)

        reset_string_action: QAction = self.addAction(
            qta.icon("ri.arrow-go-back-line", color="#ffffff"),
            self.tr("Reset selected String(s)"),
        )
        reset_string_action.setShortcut(QKeySequence("F4"))
        reset_string_action.triggered.connect(self.reset_translation_requested.emit)

        self.addSeparator()

    def __init_mark_actions(self) -> None:
        status_shortcuts: dict[String.Status, QKeySequence] = {
            String.Status.TranslationComplete: QKeySequence("F1"),
            String.Status.TranslationIncomplete: QKeySequence("F2"),
            String.Status.NoTranslationRequired: QKeySequence("F3"),
        }

        for status in String.Status:
            # Skip NoneStatus
            if status == String.Status.NoneStatus:
                continue

            mark_as_action: QAction = self.addAction(
                qta.icon(
                    "mdi6.square-rounded",
                    color=String.Status.get_color(status),
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
