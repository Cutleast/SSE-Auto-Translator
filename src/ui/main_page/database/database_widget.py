"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.ui.widgets.tab_widget import TabWidget
from PySide6.QtCore import Signal

from core.config.app_config import AppConfig
from core.database.database import TranslationDatabase
from core.database.translation import Translation
from core.downloader.download_manager import DownloadManager
from core.mod_instance.mod_instance import ModInstance
from core.mod_instance.state_service import StateService
from core.scanner.scanner import Scanner
from core.translation_provider.provider import TranslationProvider

from .downloads.downloads_tab import DownloadsTab
from .translations.translations_tab import TranslationsTab


class DatabaseWidget(TabWidget):
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
        provider: TranslationProvider,
        mod_instance: ModInstance,
        app_config: AppConfig,
        scanner: Scanner,
        download_manager: DownloadManager,
        state_service: StateService,
    ) -> None:
        """
        Args:
            database (TranslationDatabase): The translation database.
            provider (TranslationProvider): The translation provider.
            mod_instance (ModInstance): The loaded mod instance.
            app_config (AppConfig): The application configuration.
            scanner (Scanner): The scanner instance.
            download_manager (DownloadManager): The download manager.
            state_service (StateService): The state service.
        """

        super().__init__()

        self.tabBar().setDocumentMode(True)

        self.__translations_tab = TranslationsTab(
            database=database,
            provider=provider,
            mod_instance=mod_instance,
            app_config=app_config,
            scanner=scanner,
            download_manager=download_manager,
            state_service=state_service,
        )
        self.addTab(self.__translations_tab, self.tr("Translations"))

        self.__downloads_tab = DownloadsTab(download_manager, provider)
        self.addTab(self.__downloads_tab, self.tr("Downloads"))

        self.__translations_tab.edit_translation_requested.connect(
            self.edit_translation_requested.emit
        )

        database.update_signal.connect(self.update)

    def set_name_filter(self, name_filter: str, case_sensitive: bool) -> None:
        """
        Sets the name filter.

        Args:
            name_filter (str): The name to filter by.
            case_sensitive (bool): Case sensitivity.
        """

        self.__translations_tab.set_name_filter(name_filter, case_sensitive)

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
