"""
Copyright (c) Cutleast
"""

import logging
import traceback
from pathlib import Path
from queue import Empty, Queue
from typing import Optional

from PySide6.QtCore import QThread

from app_context import AppContext
from core.config.app_config import AppConfig
from core.database.database import TranslationDatabase
from core.database.translation import Translation
from core.downloader.downloader import Downloader
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
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

    running: bool = False
    paused: bool = False

    download_queue: Queue[tuple[FileDownload, ProgressCallback]]
    downloader: Downloader
    app_config: AppConfig
    provider: Provider
    database: TranslationDatabase

    def __init__(
        self,
        installer_queue: Queue[tuple[FileDownload, ProgressCallback]],
        thread_id: int,
    ) -> None:
        super().__init__()

        self.log = logging.getLogger(f"DownloaderThread-{thread_id}")

        self.download_queue = installer_queue

        self.downloader = Downloader()
        self.app_config = AppContext.get_app().app_config
        self.provider = AppContext.get_app().provider
        self.database = AppContext.get_app().database

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

        self.log.info(f"Processing download {download.file_name!r}...")

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

        if download.file_name is None:
            raise DownloadFailedError

        file_name: str = download.file_name
        url: str = self.provider.request_download(download.mod_id, download.file_id)

        downloads_folder: Path = (
            self.app_config.downloads_path or AppContext.get_app().get_tmp_dir()
        )
        mod_file: Path = downloads_folder / file_name

        if not mod_file.is_file():
            self.downloader.download(
                url, downloads_folder, file_name, progress_callback
            )
            self.log.info(f"Downloaded translation to {str(mod_file)!r}.")
        else:
            self.log.info("Translation already downloaded.")

        if mod_file.is_file():
            self.__install_translation(download, mod_file, progress_callback)
        else:
            raise DownloadFailedError()

        self.log.info("Processing complete.")
        progress_callback(ProgressUpdate(1, 1, ProgressUpdate.Status.Finished))

    def __install_translation(
        self,
        download: FileDownload,
        downloaded_file: Path,
        progress_callback: ProgressCallback,
    ) -> None:
        self.log.info("Installing translation...")
        progress_callback(ProgressUpdate(0, 0, self.tr("Installing translation...")))

        mod_instance: ModInstance = AppContext.get_app().mod_instance

        try:
            strings = self.database.importer.extract_strings_from_archive(
                downloaded_file
            )
        except Exception as ex:
            raise InstallationFailedError from ex

        else:
            original_mod: Optional[Mod] = download.original_mod

            if original_mod is None and strings:
                plugin_name = list(strings.keys())[0].lower()

                for mod in mod_instance.mods:
                    if any(
                        plugin_name == plugin.name.lower() for plugin in mod.plugins
                    ):
                        original_mod = mod

            if original_mod is None:
                raise NoOriginalModFound

            if strings:
                translation_details = self.provider.get_details(
                    mod_id=download.mod_id,
                    file_id=download.file_id,
                    source=download.source,
                )
                translation = Translation(
                    name=download.display_name,
                    path=(
                        self.database.userdb_path
                        / self.database.language
                        / download.display_name
                    ),
                    mod_id=download.mod_id,
                    file_id=download.file_id,
                    version=translation_details["version"],
                    original_mod_id=original_mod.mod_id,
                    original_file_id=original_mod.file_id,
                    original_version=original_mod.version,
                    _strings=strings,
                    status=Translation.Status.Ok,
                    source=download.source,
                    timestamp=translation_details["timestamp"],
                )
                translation.save_translation()
                self.database.add_translation(translation)

                self.database.importer.extract_additional_files(
                    downloaded_file, original_mod, translation
                )
            else:
                raise MappingFailedError

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

            try:
                self.__process_download(download, progress_callback)
            except Exception as ex:
                progress_callback(
                    ProgressUpdate(0, 1, traceback.format_exc().splitlines()[-1])
                )
                self.log.error(
                    f"Failed to process translation {download.file_name!r}: {ex}",
                    exc_info=ex,
                )

            self.download_queue.task_done()

        self.running = False
        self.log.info("Thread stopped.")
