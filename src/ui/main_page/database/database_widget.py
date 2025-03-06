"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import override

from PySide6.QtWidgets import QTabWidget

from app_context import AppContext
from core.database.database import TranslationDatabase

from .downloads.downloads_tab import DownloadsTab
from .translations.translations_tab import TranslationsTab


class DatabaseWidget(QTabWidget):
    """
    Widget for translation database and download list.
    """

    def __init__(self) -> None:
        super().__init__()

        self.tabBar().setDocumentMode(True)

        self.translations_tab = TranslationsTab()
        self.addTab(self.translations_tab, self.tr("Translations"))

        self.downloads_tab = DownloadsTab()
        self.addTab(self.downloads_tab, self.tr("Downloads"))

        AppContext.get_app().ready_signal.connect(self.__post_init)

    def __post_init(self) -> None:
        database: TranslationDatabase = AppContext.get_app().database
        database.update_signal.connect(self.update)

    def set_name_filter(self, name_filter: tuple[str, bool]) -> None:
        """
        Sets the name filter.

        Args:
            name_filter (tuple[str, bool]): The name to filter by and case-sensitivity.
        """

        self.translations_tab.set_name_filter(name_filter)

    @override
    def update(self) -> None:
        """
        Updates the displayed database.
        """

        self.translations_tab.update()
        self.downloads_tab.update()
