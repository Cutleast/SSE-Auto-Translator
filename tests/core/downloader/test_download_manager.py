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
from core.database.translation import Translation
from core.downloader.download_manager import DownloadManager
from core.downloader.file_download import FileDownload
from core.translation_provider.mod_details import ModDetails
from core.translation_provider.nm_api.nxm_id import NxmModId
from core.translation_provider.provider import TranslationProvider
from core.translation_provider.source import Source
from core.user_data.user_data import UserData
from tests.base_test import BaseTest


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
    def download_manager(
        self,
        user_data: UserData,
        app_config: AppConfig,
        provider: MagicMock,
        tmp_path: Path,
    ) -> Generator[DownloadManager]:
        """
        Creates and starts a download manager and stops it after the test.

        Args:
            user_data (UserData): The test user data.
            app_config (AppConfig): The test app configuration.
            provider (MagicMock): The mocked translation provider.
            tmp_path (Path): The temporary folder of the test.

        Yields:
            DownloadManager: The running download manager.
        """

        app_config.downloads_path = tmp_path / "downloads"
        download_manager = DownloadManager(
            user_data.database,
            user_data.mod_instance,
            provider,
            app_config,
            user_data.user_config,
            user_data.masterlist,
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

    @pytest.mark.usefixtures("temp_folder_provider")
    def test_download_installs_translation(
        self,
        download_manager: DownloadManager,
        user_data: UserData,
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
        # Remove the installed translation so that it doesn't conflict with the
        # downloaded one.
        user_data.mod_instance.mods.remove(
            self.get_mod_by_name("Wet and Cold SE - German", user_data.mod_instance)
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
            for translation in user_data.database.user_translations
            if translation.name == TestDownloadManager.TRANSLATION_NAME
        )
        assert Path("wetandcold.esp") in translation.strings
        assert (translation.path / "wetandcold.esp.json").is_file()

    @pytest.mark.usefixtures("temp_folder_provider")
    def test_failed_download_is_reported(
        self,
        download_manager: DownloadManager,
        user_data: UserData,
        requests_mock: RequestsMock,
        qtbot: QtBot,
    ) -> None:
        """
        Tests that a failing download is reported and does not change the database.
        """

        # given
        requests_mock.get(TestDownloadManager.DOWNLOAD_URL, status_code=404)
        translations_before: int = len(user_data.database.user_translations)
        download: FileDownload = TestDownloadManager.create_download()

        # when
        with qtbot.waitSignal(
            download_manager.download_failed, timeout=60_000
        ) as blocker:
            download_manager.add_download_item(download)

        # then
        assert blocker.args is not None
        assert blocker.args[0] is download
        assert len(user_data.database.user_translations) == translations_before
