"""
Copyright (c) Cutleast
"""

from typing import Optional

import qtawesome as qta
from PySide6.QtGui import QAction, QCursor, QIcon

from core.database.translation import Translation
from core.translation_provider.source import Source
from ui.widgets.menu import Menu


class TranslationsMenu(Menu):
    """
    Context menu for translations tab.
    """

    __parent: "TranslationsWidget"

    __ignore_update_action: QAction

    def __init__(self, parent: "TranslationsWidget"):
        super().__init__(parent=parent)

        self.__parent = parent

        self.__init_item_actions()
        self.__init_translation_actions()
        self.__init_open_actions()

    def __init_item_actions(self) -> None:
        expand_all_action: QAction = self.addAction(
            qta.icon("mdi6.arrow-expand-vertical", color=self.palette().text().color()),
            self.tr("Expand all"),
        )
        expand_all_action.triggered.connect(self.__parent.expandAll)

        collapse_all_action: QAction = self.addAction(
            qta.icon(
                "mdi6.arrow-collapse-vertical", color=self.palette().text().color()
            ),
            self.tr("Collapse all"),
        )
        collapse_all_action.triggered.connect(self.__parent.collapseAll)

        self.addSeparator()

    def __init_translation_actions(self) -> None:
        self.__ignore_update_action = self.addAction(
            qta.icon("mdi6.cloud-alert", color="#ffffff"),
            self.tr("Ignore translation update"),
        )
        self.__ignore_update_action.triggered.connect(self.__parent.ignore_update)

        show_strings_action: QAction = self.addAction(
            qta.icon("mdi6.book-open-outline", color="#ffffff"),
            self.tr("Show translation strings..."),
        )
        show_strings_action.triggered.connect(self.__parent.show_strings)

        edit_translation_action: QAction = self.addAction(
            qta.icon("mdi6.book-edit", color="#ffffff"), self.tr("Edit translation...")
        )
        edit_translation_action.triggered.connect(self.__parent.edit_translation)

        rename_translation_action: QAction = self.addAction(
            qta.icon("mdi6.rename", color="#ffffff"), self.tr("Rename translation...")
        )
        rename_translation_action.triggered.connect(self.__parent.rename_translation)

        export_translation_action: QAction = self.addAction(
            qta.icon("fa5s.share", color="#ffffff"), self.tr("Export translation...")
        )
        export_translation_action.triggered.connect(self.__parent.export_translation)

        delete_translation_action: QAction = self.addAction(
            qta.icon("mdi6.delete", color="#ffffff"),
            self.tr("Delete selected translation(s)..."),
        )
        delete_translation_action.triggered.connect(self.__parent.delete_translation)

        self.addSeparator()

    def __init_open_actions(self) -> None:
        self.__open_modpage_action: QAction = self.addAction(
            QIcon(":/icons/nexus_mods.svg"), self.tr("Open mod page...")
        )
        self.__open_modpage_action.triggered.connect(self.__parent.open_modpage)

        open_in_explorer_action: QAction = self.addAction(
            qta.icon("fa5s.folder", color="#ffffff"),
            self.tr("Open in Explorer..."),
        )
        open_in_explorer_action.triggered.connect(self.__parent.open_in_explorer)

    def open(self) -> None:
        """
        Opens the context menu at the current cursor position.
        """

        current_item: Optional[Translation | str] = self.__parent.get_current_item()

        if (
            isinstance(current_item, Translation)
            and current_item.source is not None
            and current_item.source != Source.Local
        ):
            self.__open_modpage_action.setVisible(True)
            self.__open_modpage_action.setIcon(current_item.source.get_icon())  # type: ignore[arg-type]
        else:
            self.__open_modpage_action.setVisible(False)

        self.__ignore_update_action.setVisible(
            isinstance(current_item, Translation)
            and current_item.status == Translation.Status.UpdateAvailable
        )

        self.exec(QCursor.pos())


if __name__ == "__main__":
    from .translations_widget import TranslationsWidget
