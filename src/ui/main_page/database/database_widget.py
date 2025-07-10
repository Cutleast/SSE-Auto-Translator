"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import override

from PySide6.QtWidgets import QTabWidget

from core.config.app_config import AppConfig
from core.database.database import TranslationDatabase
from core.downloader.download_manager import DownloadManager
from core.mod_instance.mod_instance import ModInstance
from core.scanner.scanner import Scanner
from core.translation_provider.nm_api.nxm_handler import NXMHandler
from core.translation_provider.provider import Provider

from .downloads.downloads_tab import DownloadsTab
from .translations.translations_tab import TranslationsTab


class DatabaseWidget(QTabWidget):
    """
    Widget for translation database and download list.
    """

    def __init__(
        self,
        database: TranslationDatabase,
        provider: Provider,
        mod_instance: ModInstance,
        app_config: AppConfig,
        scanner: Scanner,
        download_manager: DownloadManager,
        nxm_listener: NXMHandler,
    ) -> None:
        super().__init__()

        self.tabBar().setDocumentMode(True)

        self.translations_tab = TranslationsTab(
            database,
            provider,
            mod_instance,
            app_config,
            scanner,
            download_manager,
            nxm_listener,
        )
        self.addTab(self.translations_tab, self.tr("Translations"))

        self.downloads_tab = DownloadsTab(download_manager, provider, nxm_listener)
        self.addTab(self.downloads_tab, self.tr("Downloads"))

        database.update_signal.connect(self.update)

    def set_name_filter(self, name_filter: tuple[str, bool]) -> None:
        """
        Sets the name filter.

        Args:
            name_filter (tuple[str, bool]): The name to filter by and case-sensitivity.
        """

        self.translations_tab.set_name_filter(name_filter)

    @override
    def update(self) -> None:  # type: ignore
        """
        Updates the displayed database.
        """

        self.translations_tab.update()
        self.downloads_tab.update()
