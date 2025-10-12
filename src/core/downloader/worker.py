"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path
from queue import Empty, Queue
from typing import Optional, override

from PySide6.QtCore import QThread, Signal

from core.config.app_config import AppConfig
from core.config.user_config import UserConfig
from core.database.database import TranslationDatabase
from core.database.database_service import DatabaseService
from core.database.importer import Importer
from core.database.translation import Translation
from core.downloader.downloader import Downloader
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.string import StringList
from core.translation_provider.provider import Provider
from core.utilities.exceptions import (
    DownloadFailedError,
    InstallationFailedError,
    MappingFailedError,
    NoOriginalModFound,
)
from core.utilities.progress_update import ProgressCallback, ProgressUpdate

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

    download_finished = Signal(FileDownload)
    """
    This signal gets emitted everytime the worker finishes a download.
    """

    download_queue: Queue[tuple[FileDownload, ProgressCallback]]
    downloader: Downloader
    app_config: AppConfig
    user_config: UserConfig
    provider: Provider
    database: TranslationDatabase
    mod_instance: ModInstance

    def __init__(
        self,
        installer_queue: Queue[tuple[FileDownload, ProgressCallback]],
        thread_id: int,
        app_config: AppConfig,
        user_config: UserConfig,
        provider: Provider,
        database: TranslationDatabase,
        mod_instance: ModInstance,
    ) -> None:
        super().__init__()

        self.log = logging.getLogger(f"DownloaderThread-{thread_id}")

        self.download_queue = installer_queue

        self.downloader = Downloader()
        self.app_config = app_config
        self.user_config = user_config
        self.provider = provider
        self.database = database
        self.mod_instance = mod_instance

    def __process_download(
        self, download: FileDownload, progress_callback: ProgressCallback
    ) -> None:
        """
        Processes a file download.

        Args:
            download (FileDownload): File to download.
            progress_callback (ProgressCallback):
                Method or function that is called with a `ProgressUpdate`.
        """

        file_name: str = download.mod_details.file_name

        self.log.info(f"Processing download '{file_name}'...")

        if self.provider.direct_downloads_possible():
            self.log.info("Downloading translation...")
            progress_callback(
                ProgressUpdate(0, 0, self.tr("Downloading translation..."))
            )

        else:
            self.log.info("Waiting for free download to be started...")
            progress_callback(
                ProgressUpdate(0, 0, ProgressUpdate.Status.UserActionRequired)
            )

        self.waiting = True
        url: str = self.provider.request_download(
            download.mod_details.mod_id, download.source
        )
        self.waiting = False

        downloads_folder: Path = (
            self.app_config.downloads_path or self.app_config.get_tmp_dir()
        )
        mod_file: Path = downloads_folder / file_name

        if not mod_file.is_file():
            self.downloader.download(
                url,
                downloads_folder,
                self.provider.user_agent,
                file_name,
                progress_callback,
            )
            self.log.info(f"Downloaded translation to '{mod_file}'.")
        else:
            self.log.info("Translation already downloaded.")

        if mod_file.is_file():
            self.__install_translation(download, mod_file, progress_callback)
        else:
            raise DownloadFailedError()

        self.log.info("Processing complete.")
        self.download_finished.emit(download)
        progress_callback(ProgressUpdate(1, 1, ProgressUpdate.Status.Finished))

    def __install_translation(
        self,
        download: FileDownload,
        downloaded_file: Path,
        progress_callback: ProgressCallback,
    ) -> None:
        self.log.info("Installing translation...")
        progress_callback(ProgressUpdate(0, 0, self.tr("Installing translation...")))

        try:
            strings: dict[Path, StringList] = Importer().extract_strings_from_archive(
                downloaded_file,
                self.mod_instance,
                self.app_config.get_tmp_dir(),
                self.database.language,
            )
        except Exception as ex:
            raise InstallationFailedError from ex

        if not strings:
            raise MappingFailedError

        # TODO: Improve this to work with modfiles from multiple original mods or to get at least the original mod with the most mod files
        modfile: Path = list(strings.keys())[0]
        original_mod: Optional[Mod] = self.mod_instance.get_mod_with_modfile(
            modfile,
            ignore_states=[
                TranslationStatus.TranslationInstalled,
                TranslationStatus.IsTranslated,
            ],
        )

        if original_mod is None:
            raise NoOriginalModFound

        translation = Translation(
            name=download.mod_details.display_name,
            path=(
                self.database.userdb_path
                / self.database.language.id
                / download.mod_details.display_name
            ),
            mod_id=download.mod_details.mod_id,
            version=download.mod_details.version,
            original_mod_id=original_mod.mod_id,
            original_version=original_mod.version,
            status=Translation.Status.Ok,
            source=download.source,
            timestamp=download.mod_details.timestamp,
        )
        translation.strings = strings
        translation.save()
        DatabaseService.add_translation(translation, self.database)

        Importer().extract_additional_files(
            archive_path=downloaded_file,
            original_mod=original_mod,
            translation_path=translation.path,
            tmp_dir=self.app_config.get_tmp_dir(),
            user_config=self.user_config,
        )

    @override
    def run(self) -> None:
        self.log.info("Thread started.")
        self.running = True

        while self.running:
            if self.paused:
                self.log.info("Thread paused.")
                self.running = False

                while self.paused:
                    pass

                self.running = True
                self.log.info("Thread continued.")

            try:
                # Wait at max 1 second for a download or just repeat the loop
                # while the thread is set to running
                download, progress_callback = self.download_queue.get(timeout=1)
            except Empty:
                continue

            if not download.stale:
                self.processing = True
                try:
                    self.__process_download(download, progress_callback)
                except Exception as ex:
                    progress_callback(
                        ProgressUpdate(1, 1, ProgressUpdate.Status.Failed, exception=ex)
                    )
                    self.log.error(
                        f"Failed to process translation '{download.mod_details.file_name}':"
                        f" {ex}",
                        exc_info=ex,
                    )
                self.processing = False
            else:
                self.download_finished.emit(download)
                progress_callback(ProgressUpdate(1, 1, ProgressUpdate.Status.Finished))

            self.download_queue.task_done()
            self.task_done.emit()

        self.running = False
        self.log.info("Thread stopped.")
