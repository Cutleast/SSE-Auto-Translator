"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import override

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTabWidget

from core.config.app_config import AppConfig
from core.database.database import TranslationDatabase
from core.database.translation import Translation
from core.downloader.download_manager import DownloadManager
from core.mod_instance.mod_instance import ModInstance
from core.scanner.scanner import Scanner
from core.translation_provider.provider import Provider

from .downloads.downloads_tab import DownloadsTab
from .translations.translations_tab import TranslationsTab


class DatabaseWidget(QTabWidget):
    """
    Widget for translation database and download list.
    """

    edit_translation_requested = Signal(Translation)
    """
    Signal emitted when the user requests to edit a translation.

    Args:
        Translation: Translation to edit.
    """

    __translations_tab: TranslationsTab
    __downloads_tab: DownloadsTab

    def __init__(
        self,
        database: TranslationDatabase,
        provider: Provider,
        mod_instance: ModInstance,
        app_config: AppConfig,
        scanner: Scanner,
        download_manager: DownloadManager,
    ) -> None:
        super().__init__()

        self.tabBar().setDocumentMode(True)

        self.__translations_tab = TranslationsTab(
            database,
            provider,
            mod_instance,
            app_config,
            scanner,
            download_manager,
        )
        self.addTab(self.__translations_tab, self.tr("Translations"))

        self.__downloads_tab = DownloadsTab(download_manager, provider)
        self.addTab(self.__downloads_tab, self.tr("Downloads"))

        self.__translations_tab.edit_translation_requested.connect(
            self.edit_translation_requested.emit
        )

        database.update_signal.connect(self.update)

    def set_name_filter(self, name_filter: tuple[str, bool]) -> None:
        """
        Sets the name filter.

        Args:
            name_filter (tuple[str, bool]): The name to filter by and case-sensitivity.
        """

        self.__translations_tab.set_name_filter(name_filter)

    @override
    def update(self) -> None:  # type: ignore
        """
        Updates the displayed database.
        """

        self.__translations_tab.update()
        self.__downloads_tab.update()

    def highlight_translation(self, translation: Translation) -> None:
        """
        Highlights the specified translation by selecting it in the translations tab.

        Args:
            translation (Translation): Translation to highlight.
        """

        self.__translations_tab.highlight_translation(translation)
