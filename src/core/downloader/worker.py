"""
Copyright (c) Cutleast
"""

import logging
import time
from pathlib import Path
from queue import Empty, Queue
from typing import override

from cutleast_core_lib.core.downloader import Downloader
from cutleast_core_lib.core.multithreading.progress import (
    ProgressUpdate,
    UpdateCallback,
)
from PySide6.QtCore import QThread, Signal

from core.config.app_config import AppConfig
from core.config.user_config import UserConfig
from core.database.database import TranslationDatabase
from core.database.database_service import DatabaseService
from core.database.translation import Translation
from core.mod_instance.mod_instance import ModInstance
from core.string.string_extractor import StringExtractor
from core.string.types import StringList
from core.translation_provider.nm_api.nm_api import NexusModsApi
from core.translation_provider.nm_api.nxm_id import NxmModId
from core.translation_provider.provider import TranslationProvider
from core.translation_provider.source import Source
from core.utilities.exceptions import (
    DownloadFailedError,
    InstallationFailedError,
    NoStringsExtractedError,
)
from core.utilities.temp_folder_provider import TempFolderProvider

from .file_download import FileDownload


class Worker(QThread):
    """
    Class for worker thread of downloader.
    """

    log: logging.Logger

    processing: bool = False
    running: bool = False
    paused: bool = False
    waiting: bool = False

    task_done = Signal()
    """
    This signal gets emitted everytime the worker finishes a task.
    """

    download_started = Signal(FileDownload)
    """
    This signal gets emitted everytime the worker starts a download.

    Args:
        FileDownload: The download that was started.
    """

    download_finished = Signal(FileDownload)
    """
    This signal gets emitted everytime the worker finishes a download.

    Args:
        FileDownload: The download that was finished.
    """

    user_action_required = Signal(FileDownload, str)
    """
    This signal gets emitted everytime the worker requires user action to continue a
    download.

    Args:
        FileDownload: The download that requires user action.
        str: The download URL to open.
    """

    download_failed = Signal(FileDownload, Exception)
    """
    This signal gets emitted everytime the worker fails a download.

    Args:
        FileDownload: The download that failed.
        Exception: The exception that caused the failure.
    """

    download_queue: Queue[tuple[FileDownload, UpdateCallback]]
    downloader: Downloader
    app_config: AppConfig
    user_config: UserConfig
    provider: TranslationProvider
    database: TranslationDatabase
    mod_instance: ModInstance

    def __init__(
        self,
        installer_queue: Queue[tuple[FileDownload, UpdateCallback]],
        thread_id: int,
        app_config: AppConfig,
        user_config: UserConfig,
        provider: TranslationProvider,
        database: TranslationDatabase,
        mod_instance: ModInstance,
    ) -> None:
        """
        Args:
            installer_queue (Queue[tuple[FileDownload, UpdateCallback]]):
                Queue of downloads to process. Each item is a tuple of a `FileDownload`
                and a `UpdateCallback`.
            thread_id (int): ID of the thread.
            app_config (AppConfig): The application configuration.
            user_config (UserConfig): The user configuration.
            provider (TranslationProvider): The translation provider.
            database (TranslationDatabase): The translation database.
            mod_instance (ModInstance): The loaded mod instance.
        """

        super().__init__()

        self.log = logging.getLogger(f"DownloaderThread-{thread_id}")

        self.download_queue = installer_queue

        self.downloader = Downloader(provider.user_agent)
        self.app_config = app_config
        self.user_config = user_config
        self.provider = provider
        self.database = database
        self.mod_instance = mod_instance

    def __process_download(
        self, download: FileDownload, update_callback: UpdateCallback
    ) -> None:
        """
        Processes a file download.

        Args:
            download (FileDownload): File to download.
            update_callback (UpdateCallback):
                Method or function that is called with a `ProgressUpdate`.
        """

        file_name: str = download.mod_details.file_name

        self.log.info(f"Processing download '{file_name}'...")

        downloads_folder: Path = (
            self.app_config.downloads_path or TempFolderProvider.get().get_temp_folder()
        )
        downloads_folder.mkdir(parents=True, exist_ok=True)
        mod_file: Path = downloads_folder / file_name

        if not mod_file.is_file():
            if not self.provider.direct_downloads_possible(download.source):
                if download.source == Source.NexusMods:
                    self.log.info("Waiting for free download to be started...")
                    assert isinstance(download.mod_details.mod_id, NxmModId)

                    nxm_url: str = NexusModsApi.create_nexus_mods_url(
                        game_id=download.mod_details.mod_id.nm_game_id,
                        mod_id=download.mod_details.mod_id.mod_id,
                        file_id=download.mod_details.mod_id.file_id,
                        mod_manager=True,
                    )
                    self.user_action_required.emit(download, nxm_url)

                else:
                    raise DownloadFailedError

            self.waiting = True
            url: str = self.provider.request_download(
                download.mod_details.mod_id, download.source
            )
            self.waiting = False

            self.log.info("Downloading translation...")
            update_callback(
                ProgressUpdate(
                    status_text=self.tr("Downloading translation..."), value=0, maximum=0
                )
            )
            self.download_started.emit(download)

            self.downloader.download(url, downloads_folder, file_name, update_callback)
            self.log.info(f"Downloaded translation to '{mod_file}'.")
        else:
            self.log.info("Translation already downloaded.")

        if mod_file.is_file():
            self.__install_translation(download, mod_file, update_callback)
        else:
            raise DownloadFailedError

        self.log.info("Processing complete.")
        self.download_finished.emit(download)

    def __install_translation(
        self,
        download: FileDownload,
        downloaded_file: Path,
        update_callback: UpdateCallback,
    ) -> None:
        self.log.info("Installing translation...")
        update_callback(
            ProgressUpdate(
                status_text=self.tr("Installing translation..."), value=0, maximum=0
            )
        )

        try:
            strings: dict[Path, StringList] = StringExtractor().extract_strings(
                input=downloaded_file,
                mod_instance=self.mod_instance,
                language=self.database.language,
                max_workers=self.app_config.worker_thread_num,
            )
        except Exception as ex:
            raise InstallationFailedError from ex

        if not strings:
            raise NoStringsExtractedError

        translation = Translation(
            name=download.mod_details.display_name,
            path=(
                self.database.userdb_path
                / self.database.language.id
                / download.mod_details.display_name
            ),
            mod_id=download.mod_details.mod_id,
            version=download.mod_details.version,
            source=download.source,
            timestamp=download.mod_details.timestamp,
        )
        translation.strings = strings
        translation.save()
        DatabaseService.add_translation(translation, self.database)

    @override
    def run(self) -> None:
        self.log.info("Thread started.")
        self.running = True

        while self.running:
            if self.paused:
                self.log.info("Thread paused.")
                self.running = False

                while self.paused:
                    time.sleep(0.01)

                self.running = True
                self.log.info("Thread continued.")

            try:
                # Wait at max 1 second for a download or just repeat the loop
                # while the thread is set to running
                download, update_callback = self.download_queue.get(timeout=1)
            except Empty:
                continue

            if not download.stale:
                self.processing = True
                try:
                    self.__process_download(download, update_callback)
                except Exception as ex:
                    self.log.error(
                        f"Failed to process translation '{download.mod_details.file_name}':"
                        f" {ex}",
                        exc_info=ex,
                    )
                    self.download_failed.emit(download, ex)

                self.processing = False
            else:
                self.download_finished.emit(download)

            self.download_queue.task_done()
            self.task_done.emit()

        self.running = False
        self.log.info("Thread stopped.")
