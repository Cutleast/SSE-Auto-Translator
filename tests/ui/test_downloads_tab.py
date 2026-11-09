"""
Copyright (c) Cutleast
"""

from pathlib import Path

from cutleast_core_lib.test.utils import Utils
from PySide6.QtGui import QAction
from pytest_mock import MockerFixture
from pytestqt.qtbot import QtBot

from core.config.app_config import AppConfig
from core.config.user_config import UserConfig
from core.downloader.download_manager import DownloadManager
from core.translation_provider.provider import TranslationProvider
from core.translation_provider.provider_preference import ProviderPreference
from core.utilities.temp_folder_provider import TempFolderProvider
from tests.base_test import BaseTest
from tests.setup.data_factory import DataFactory
from ui.main_page.database.downloads.downloads_tab import DownloadsTab
from ui.main_page.database.downloads.downloads_toolbar import DownloadsToolbar


class TestDownloadsTab(BaseTest):
    """
    Tests `ui.main_page.database.downloads.downloads_tab.DownloadsTab`.
    """

    HANDLE_NXM_ACTION: tuple[str, type[QAction]] = "handle_nxm_action", QAction
    """Identifier for accessing the Nexus Mods action."""

    TOOLBAR: tuple[str, type[DownloadsToolbar]] = "toolbar", DownloadsToolbar
    """Identifier for accessing the downloads toolbar."""

    def test_initializes_without_provider(
        self,
        app_config: AppConfig,
        temp_folder_provider: TempFolderProvider,
        tmp_path: Path,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        """
        Tests initialization when no Nexus Mods API is available.

        Args:
            app_config (AppConfig): Application configuration.
            temp_folder_provider (TempFolderProvider): The temp folder provider.
            tmp_path (Path): The temporary folder of the test.
            qtbot (QtBot): Fixture for Qt widgets.
            mocker (MockerFixture): Fixture for mocking dependencies.
        """

        # given
        user_config: UserConfig = DataFactory.user_config()
        user_config.provider_preference = ProviderPreference.OnlyNexusMods
        mocker.patch(
            "core.translation_provider.provider_manager.NexusModsApi",
            side_effect=RuntimeError,
        )
        provider = TranslationProvider(user_config)
        download_manager = DownloadManager(
            database=DataFactory.database(tmp_path),
            mod_instance=DataFactory.mod_instance([]),
            provider=provider,
            app_config=app_config,
            user_config=user_config,
            masterlist=DataFactory.masterlist(),
            temp_folder_provider=temp_folder_provider,
        )

        # when
        widget = DownloadsTab(download_manager, provider)
        qtbot.addWidget(widget)

        # then
        toolbar: DownloadsToolbar = Utils.get_private_field(
            widget, *TestDownloadsTab.TOOLBAR
        )
        handle_nxm_action: QAction = Utils.get_private_field(
            toolbar, *TestDownloadsTab.HANDLE_NXM_ACTION
        )
        assert not handle_nxm_action.isEnabled()
