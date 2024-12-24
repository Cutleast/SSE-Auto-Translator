"""
Copyright (c) Cutleast
"""

import qtawesome as qta
from PySide6.QtGui import QAction, QCursor, QKeySequence

from core.database.string import String
from ui.widgets.menu import Menu


class EditorMenu(Menu):
    """
    Context menu for editor tab.
    """

    __parent: "EditorTab"

    def __init__(self, parent: "EditorTab"):
        super().__init__(parent=parent)

        self.__parent = parent

        self.__init_actions()
        self.__init_mark_actions()

    def __init_actions(self) -> None:
        open_translator_action: QAction = self.addAction(
            qta.icon("mdi6.rename", color="#ffffff"), self.tr("Edit String...")
        )
        open_translator_action.triggered.connect(
            lambda _: self.__parent.open_translator_dialog()
        )

        copy_action: QAction = self.addAction(
            qta.icon("mdi6.content-copy", color="#ffffff"), self.tr("Copy String")
        )
        copy_action.setIconVisibleInMenu(True)
        copy_action.triggered.connect(lambda _: self.__parent.copy_selected())

        reset_translation_action: QAction = self.addAction(
            qta.icon("ri.arrow-go-back-line", color="#ffffff"),
            self.tr("Reset selected String(s)"),
        )
        reset_translation_action.setShortcut(QKeySequence("F4"))
        reset_translation_action.triggered.connect(
            lambda _: self.__parent.reset_translation()
        )

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
                lambda _, s=status: self.__parent.set_status(s)
            )

        self.addSeparator()

    def open(self) -> None:
        self.exec(QCursor.pos())


if __name__ == "__main__":
    from .editor_tab import EditorTab
