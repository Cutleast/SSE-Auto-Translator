"""
Copyright (c) Cutleast
"""

import qtawesome as qta
from PySide6.QtCore import QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar


class TranslationsToolbar(QToolBar):
    """
    Toolbar for translations tab.
    """

    __parent: "TranslationsTab"

    update_action: QAction

    def __init__(self, parent: "TranslationsTab"):
        super().__init__(parent)

        self.__parent = parent

        self.setIconSize(QSize(32, 32))
        self.setFloatable(False)

        self.__init_actions()

    def __init_actions(self) -> None:
        show_vanilla_strings_action: QAction = self.addAction(
            qta.icon("mdi6.book-open-outline", color="#ffffff"),
            self.tr("Show base game (+ AE CC content) strings"),
        )
        show_vanilla_strings_action.triggered.connect(
            lambda _: self.__parent.show_vanilla_strings()
        )

        search_database_action: QAction = self.addAction(
            qta.icon("fa.search", color="#ffffff", scale_factor=0.85),
            self.tr("Search database"),
        )
        search_database_action.triggered.connect(
            lambda _: self.__parent.search_database()
        )

        self.addSeparator()

        local_import_action: QAction = self.addAction(
            qta.icon("mdi6.import", color="#ffffff"),
            self.tr("Import translation from local disk"),
        )
        local_import_action.triggered.connect(
            lambda _: self.__parent.import_local_translation()
        )

        update_check_action: QAction = self.addAction(
            qta.icon("mdi6.cloud-refresh", color="#ffffff"),
            self.tr("Check translations for available updates"),
        )
        update_check_action.triggered.connect(
            lambda _: self.__parent.check_for_updates()
        )

        self.update_action = self.addAction(
            qta.icon("mdi6.cloud-download", color="#ffffff"),
            self.tr("Download and install available translation updates"),
        )
        self.update_action.setDisabled(True)
        self.update_action.triggered.connect(lambda _: self.__parent.download_updates())


if __name__ == "__main__":
    from .translations_tab import TranslationsTab
