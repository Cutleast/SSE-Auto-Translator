"""
Copyright (c) Cutleast
"""

import logging
from concurrent.futures import Future, as_completed
from pathlib import Path
from queue import Queue
from typing import Optional, TypeAlias

from cutleast_core_lib.core.multithreading.progress import (
    ProgressUpdate,
    UpdateCallback,
    update,
)
from cutleast_core_lib.core.multithreading.progress_executor import ProgressExecutor
from cutleast_core_lib.ui.progress.display import ProgressDisplay
from PySide6.QtCore import QObject, Signal

from core.config.app_config import AppConfig
from core.config.user_config import UserConfig
from core.database.database import TranslationDatabase
from core.masterlist.masterlist import Masterlist
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.translation_provider.mod_id import ModId
from core.translation_provider.provider import ModDetails, Provider
from core.translation_provider.source import Source

from .file_download import FileDownload
from .mod_info import ModInfo
from .translation_download import TranslationDownload
from .worker import Worker

DownloadListEntries: TypeAlias = dict[ModInfo, dict[Path, list[TranslationDownload]]]
"""
Type alias for download list entries. A dict of mod infos to a dict of mod file paths to
a list of available translation downloads.

```
ModInfo
└─ ModFile Path (relative to the game's "Data" folder)
   └─ TranslationDownload
      └─ FileDownload
```
"""


class DownloadManager(QObject):
    """
    Class for managing and running downloads and installations of translations.
    """

    download_added = Signal(FileDownload)
    """
    Signal emitted when a new download is added to the queue.

    Args:
        FileDownload: The download that was added to the queue.
    """

    download_started = Signal(FileDownload)
    """
    Signal emitted when a download has started.

    Args:
        FileDownload: The download that has started.
    """

    download_finished = Signal(FileDownload)
    """
    Signal emitted when a download has finished.

    Args:
        FileDownload: The download that has finished.
    """

    user_action_required = Signal(FileDownload, str)
    """
    Signal emitted when a download requires user action to continue.

    Args:
        FileDownload: The download that requires user action.
        str: The download URL to open.
    """

    download_failed = Signal(FileDownload, Exception)
    """
    Signal emitted when a download has failed.

    Args:
        FileDownload: The download that has failed.
        Exception: The exception that caused the failure.
    """

    finished = Signal()
    """
    Signal emitted when all worker threads have finished.
    """

    stopped = Signal()
    """
    Signal emitted when all worker threads have finished or have been stopped.
    """

    __thread_num: int
    __queue: Queue[tuple[FileDownload, UpdateCallback]]
    __workers: list[Worker]
    __running: bool

    __database: TranslationDatabase
    __mod_instance: ModInstance
    __provider: Provider
    __app_config: AppConfig
    __user_config: UserConfig
    __masterlist: Masterlist

    log: logging.Logger = logging.getLogger("DownloadManager")

    def __init__(
        self,
        database: TranslationDatabase,
        mod_instance: ModInstance,
        provider: Provider,
        app_config: AppConfig,
        user_config: UserConfig,
        masterlist: Masterlist,
    ) -> None:
        """
        Args:
            database (TranslationDatabase): The translation database.
            mod_instance (ModInstance): The loaded mod instance.
            provider (Provider): The translation provider.
            app_config (AppConfig): The application configuration.
            user_config (UserConfig): The user configuration.
            masterlist (Masterlist): The loaded masterlist.
        """

        super().__init__()

        self.__thread_num = app_config.download_thread_num
        self.__queue = Queue()
        self.__workers = []
        self.__running = False

        self.__database = database
        self.__mod_instance = mod_instance
        self.__provider = provider
        self.__app_config = app_config
        self.__user_config = user_config
        self.__masterlist = masterlist

        self.finished.connect(self.stopped.emit)

    def pause(self) -> None:
        """
        Pauses worker threads and blocks code until all threads are paused.
        """

        self.log.info("Pausing worker threads...")

        for worker in self.__workers:
            worker.paused = True

        while any(worker.running for worker in self.__workers):
            pass

        self.__running = False
        self.log.info("Paused worker threads.")

    def resume(self) -> None:
        """
        Unpauses worker threads.
        """

        self.log.info("Continuing worker threads...")
        self.__running = True

        for worker in self.__workers:
            worker.paused = False

        self.log.info("Continued worker threads.")

    @property
    def running(self) -> bool:
        """If the download manager is currently running."""

        return self.__running

    def start(self) -> None:
        """
        Starts worker threads (if not already running).
        """

        if self.__running or self.__workers:
            return

        self.log.debug(f"Starting {self.__thread_num} thread(s)...")

        self.__running = True

        self.__workers = [
            Worker(
                installer_queue=self.__queue,
                thread_id=i,
                app_config=self.__app_config,
                user_config=self.__user_config,
                provider=self.__provider,
                database=self.__database,
                mod_instance=self.__mod_instance,
            )
            for i in range(self.__thread_num)
        ]

        for worker in self.__workers:
            worker.task_done.connect(self.__on_worker_finished)
            worker.download_started.connect(self.download_started.emit)
            worker.download_finished.connect(self.download_finished.emit)
            worker.user_action_required.connect(self.user_action_required.emit)
            worker.download_failed.connect(self.download_failed.emit)
            worker.start()

        self.log.info("Threads started, ready for downloads.")

    def __on_worker_finished(self) -> None:
        if (
            self.__queue.qsize() == 0
            and all(not worker.processing for worker in self.__workers)
            and self.__running
        ):
            self.finished.emit()

    def join(self) -> None:
        """
        Blocks code until all mods are processed.
        """

        self.__queue.join()

    def terminate(self) -> None:
        """
        Terminates worker threads. **NOT** recommended!
        Use `DownloadManager.stop()` instead, if possible.
        """

        self.log.info("Terminating worker threads...")

        for worker in self.__workers:
            worker.terminate()

        self.__workers.clear()
        self.stopped.emit()
        self.log.info("Terminated worker threads.")

    def stop(self) -> None:
        """
        Stops worker threads and blocks code until all threads have stopped.
        """

        self.log.info("Stopping worker threads...")

        for worker in self.__workers:
            # Terminate paused workers
            if worker.paused or worker.waiting:
                worker.terminate()
            # Or signal them to stop
            else:
                worker.running = False

        while any(worker.isRunning() for worker in self.__workers):
            pass

        self.__running = False
        self.__workers.clear()
        self.stopped.emit()
        self.log.info("Stopped worker threads.")

    def request_download(self, download: FileDownload) -> None:
        """
        Requests to add a download to the queue.
        This does not add it to the queue but notify
        listeners so that they add it to the queue.

        Args:
            download (FileDownload): Download to add.
        """

        self.download_added.emit(download)

    def add_download_item(
        self, download: FileDownload, update_callback: UpdateCallback
    ) -> None:
        """
        Adds a download item to the queue.

        Args:
            download (FileDownload): Download to add.
            update_callback (UpdateCallback):
                Function or method to call with a ProgressUpdate.
        """

        self.__queue.put((download, update_callback))

    def remove_download_item(self, download: FileDownload) -> None:
        """
        Removes a download item from the queue. This does not cancel it
        if it is already running and just set its `stale` flag to `True`.

        Args:
            download (FileDownload): Download to remove.
        """

        download.stale = True

    def collect_available_downloads(
        self,
        items: dict[Mod, list[ModFile]],
        pdisplay: Optional[ProgressDisplay] = None,
    ) -> DownloadListEntries:
        """
        Collects downloads for required translations that are available online.

        Args:
            items (dict[Mod, list[ModFile]]): The items to collect downloads for.
            pdisplay (Optional[ProgressDisplay], optional):
                Optional progress display. Defaults to None.

        Returns:
            DownloadListEntries:
                Dictionary of mod-file combinations and their downloads.
        """

        self.log.info("Getting downloads for required translations...")

        if pdisplay is not None:
            pdisplay.updateMainProgress(
                ProgressUpdate(status_text=self.tr("Collecting available downloads..."))
            )

        # Filter items for mod files that have an available translation
        items = {
            mod: [
                modfile
                for modfile in modfiles
                if modfile.status == TranslationStatus.TranslationAvailableOnline
            ]
            for mod, modfiles in items.items()
        }
        items = {mod: modfiles for mod, modfiles in items.items() if modfiles}

        translation_downloads: DownloadListEntries = {}
        with ProgressExecutor(
            pdisplay, max_workers=self.__app_config.worker_thread_num
        ) as executor:
            executor.set_main_progress_text(self.tr("Collecting available downloads..."))

            tasks: dict[Future[dict[Path, list[TranslationDownload]]], Mod] = {}
            for mod, modfiles in items.items():
                future: Future[dict[Path, list[TranslationDownload]]] = executor.submit(
                    # this lambda is necessary as it gets an update callable as first
                    # positional argument
                    lambda ucb, m=mod, mfs=modfiles: self.__collect_downloads_for_mod(
                        m, mfs, ucb
                    )
                )
                tasks[future] = mod

            for future in as_completed(tasks):
                mod: Mod = tasks[future]
                try:
                    mod_info = ModInfo(
                        display_name=mod.name + f" [{mod.version}]",
                        mod_id=mod.mod_id,
                        source=(
                            Source.NexusMods if mod.mod_id is not None else Source.Local
                        ),
                    )

                    download_units: dict[Path, list[TranslationDownload]] = (
                        future.result()
                    )

                    for modfile, downloads in download_units.items():
                        if downloads:
                            translation_downloads.setdefault(mod_info, {})[modfile] = (
                                downloads
                            )
                except Exception as ex:
                    self.log.error(
                        f"Failed to collect downloads for {mod.name}: {ex}", exc_info=ex
                    )
                    continue

        self.log.info("Download collection complete.")

        return translation_downloads

    def __collect_downloads_for_mod(
        self,
        mod: Mod,
        modfiles: list[ModFile],
        update_callback: Optional[UpdateCallback] = None,
    ) -> dict[Path, list[TranslationDownload]]:
        download_units: dict[Path, list[TranslationDownload]] = {}
        for m, modfile in enumerate(modfiles):
            update(
                update_callback,
                ProgressUpdate(
                    status_text=f"{mod.name} > {modfile.name} ({m}/{len(modfiles)})",
                    value=m,
                    maximum=len(modfiles),
                ),
            )

            try:
                modfile_downloads: list[TranslationDownload] = (
                    self.__collect_downloads_for_modfile(mod, modfile)
                )
                if modfile_downloads:
                    download_units[modfile.path] = modfile_downloads
            except Exception as ex:
                self.log.error(
                    f"Failed to collect downloads for '{mod.name}' > '{modfile.name}': "
                    + str(ex),
                    exc_info=ex,
                )

        return download_units

    def __collect_downloads_for_modfile(
        self, mod: Mod, modfile: ModFile
    ) -> list[TranslationDownload]:
        if mod.mod_id is None:
            return []

        available_translations: dict[Source, list[ModId]] = (
            self.__provider.get_translations(
                mod.mod_id,
                modfile.name,
                self.__user_config.language.id,
                self.__masterlist,
                self.__user_config.author_blacklist,
            )
        )

        # Use a dict to group translation files from the same mod and source together
        translation_downloads: dict[tuple[int, Source], TranslationDownload] = {}
        for source, translation_ids in available_translations.items():
            for translation_id in translation_ids:
                try:
                    file_details: ModDetails = self.__provider.get_details(
                        translation_id, source
                    )
                except Exception as ex:
                    self.log.error(
                        f"Failed to get details for {translation_id}: {ex}",
                        exc_info=ex,
                    )
                    continue

                download = FileDownload(mod_details=file_details, source=source)
                translation_name: str = (
                    file_details.mod_display_name or file_details.display_name
                )
                translation_download = TranslationDownload(
                    mod_info=ModInfo(
                        display_name=translation_name,
                        mod_id=translation_id,
                        source=source,
                    ),
                    available_downloads=[],
                )
                translation_downloads.setdefault(
                    (translation_id.mod_id, source), translation_download
                ).available_downloads.append(download)

        result: list[TranslationDownload] = list(translation_downloads.values())
        return result
