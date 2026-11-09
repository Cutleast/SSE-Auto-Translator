"""
Copyright (c) Cutleast
"""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytestqt.qtbot import QtBot
from requests_mock import Mocker as RequestsMock

from core.config.app_config import AppConfig
from core.database.database import TranslationDatabase
from core.database.translation import Translation
from core.downloader.download_manager import DownloadManager
from core.downloader.file_download import FileDownload
from core.translation_provider.mod_details import ModDetails
from core.translation_provider.nm_api.nxm_id import NxmModId
from core.translation_provider.provider import TranslationProvider
from core.translation_provider.source import Source
from core.utilities.temp_folder_provider import TempFolderProvider
from tests.base_test import BaseTest
from tests.setup.data_factory import DataFactory


class TestDownloadManager(BaseTest):
    """
    Integration tests for `core.downloader.download_manager.DownloadManager` and its
    worker threads with a mocked translation provider.
    """

    DOWNLOAD_URL: str = "https://files.example.com/Wet%20and%20Cold%20SE%20-%20German.7z"
    """The (mocked) URL the test translation is downloaded from."""

    TRANSLATION_NAME: str = "Wet and Cold SE - German (Download)"
    """The name of the downloaded test translation."""

    @pytest.fixture
    def provider(self) -> MagicMock:
        """
        Returns a mocked translation provider that allows direct downloads.

        Returns:
            MagicMock: The mocked provider.
        """

        provider = MagicMock(spec=TranslationProvider)
        provider.is_available = True
        provider.direct_downloads_possible.return_value = True
        provider.request_download.return_value = TestDownloadManager.DOWNLOAD_URL
        provider.user_agent = "SSE-AT-Tests"

        return provider

    @pytest.fixture
    def database(self, tmp_path: Path) -> TranslationDatabase:
        """
        Creates an empty translation database.

        Args:
            tmp_path (Path): The temporary folder of the test.

        Returns:
            TranslationDatabase: The database.
        """

        return DataFactory.database(tmp_path)

    @pytest.fixture
    def download_manager(
        self,
        database: TranslationDatabase,
        app_config: AppConfig,
        provider: MagicMock,
        temp_folder_provider: TempFolderProvider,
        tmp_path: Path,
    ) -> Generator[DownloadManager]:
        """
        Creates and starts a download manager for a mod instance with the original mod
        of the test translation and stops it after the test.

        Args:
            database (TranslationDatabase): The translation database.
            app_config (AppConfig): The test app configuration.
            provider (MagicMock): The mocked translation provider.
            temp_folder_provider (TempFolderProvider): The temp folder provider.
            tmp_path (Path): The temporary folder of the test.

        Yields:
            DownloadManager: The running download manager.
        """

        app_config.downloads_path = tmp_path / "downloads"
        download_manager = DownloadManager(
            database,
            DataFactory.mod_instance([DataFactory.instance_mod("Wet and Cold SE")]),
            provider,
            app_config,
            DataFactory.user_config(),
            DataFactory.masterlist(),
            temp_folder_provider,
        )
        download_manager.start()

        yield download_manager

        download_manager.stop()

    @staticmethod
    def create_download() -> FileDownload:
        """
        Creates a file download for the test translation archive.

        Returns:
            FileDownload: The file download.
        """

        return FileDownload(
            mod_details=ModDetails(
                display_name=TestDownloadManager.TRANSLATION_NAME,
                file_name="Wet and Cold SE - German.7z",
                mod_id=NxmModId(mod_id=89391, file_id=504702),
                version="2.4",
                timestamp=1753462285,
                author=None,
                uploader=None,
                modpage_url="https://www.nexusmods.com/skyrimspecialedition/mods/89391",
            ),
            source=Source.NexusMods,
        )

    def test_download_installs_translation(
        self,
        download_manager: DownloadManager,
        database: TranslationDatabase,
        data_folder: Path,
        requests_mock: RequestsMock,
        qtbot: QtBot,
    ) -> None:
        """
        Tests that a downloaded translation archive is extracted and added to the
        database.
        """

        # given
        archive_data: bytes = (data_folder / "Wet and Cold SE - German.7z").read_bytes()
        requests_mock.get(
            TestDownloadManager.DOWNLOAD_URL,
            content=archive_data,
            headers={"Content-Length": str(len(archive_data))},
        )
        download: FileDownload = TestDownloadManager.create_download()
        finished: list[FileDownload] = []
        failures: list[Exception] = []
        download_manager.download_finished.connect(finished.append)
        download_manager.download_failed.connect(lambda _, ex: failures.append(ex))

        # when
        download_manager.add_download_item(download)
        qtbot.waitUntil(lambda: bool(finished or failures), timeout=60_000)

        # then
        assert failures == []
        assert finished == [download]
        translation: Translation = next(
            translation
            for translation in database.user_translations
            if translation.name == TestDownloadManager.TRANSLATION_NAME
        )
        assert Path("wetandcold.esp") in translation.strings
        assert (translation.path / "wetandcold.esp.json").is_file()

    def test_failed_download_is_reported(
        self,
        download_manager: DownloadManager,
        database: TranslationDatabase,
        requests_mock: RequestsMock,
        qtbot: QtBot,
    ) -> None:
        """
        Tests that a failing download is reported and does not change the database.
        """

        # given
        requests_mock.get(TestDownloadManager.DOWNLOAD_URL, status_code=404)
        translations_before: int = len(database.user_translations)
        download: FileDownload = TestDownloadManager.create_download()

        # when
        with qtbot.waitSignal(
            download_manager.download_failed, timeout=60_000
        ) as blocker:
            download_manager.add_download_item(download)

        # then
        assert blocker.args is not None
        assert blocker.args[0] is download
        assert len(database.user_translations) == translations_before
