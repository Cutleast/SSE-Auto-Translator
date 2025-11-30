"""
Copyright (c) Cutleast
"""

import logging
from concurrent.futures import Future, as_completed
from pathlib import Path
from queue import Queue
from typing import Optional, TypeAlias

from cutleast_core_lib.core.utilities.progress_executor import ProgressExecutor
from cutleast_core_lib.ui.widgets.loading_dialog import LoadingDialog
from cutleast_core_lib.ui.widgets.progress_dialog import (
    ProgressDialog,
    UpdateCallback,
    update,
)
from PySide6.QtCore import QObject, Signal

from core.config.app_config import AppConfig
from core.config.user_config import UserConfig
from core.database.database import TranslationDatabase
from core.database.translation import Translation
from core.masterlist.masterlist import Masterlist
from core.mod_file.mod_file import ModFile
from core.mod_file.translation_status import TranslationStatus
from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.translation_provider.mod_id import ModId
from core.translation_provider.provider import ModDetails, Provider
from core.translation_provider.source import Source
from core.utilities.progress_update import ProgressCallback

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

    log: logging.Logger = logging.getLogger("DownloadManager")

    thread_num: int
    """Number of worker threads."""

    queue: Queue[tuple[FileDownload, ProgressCallback]]
    workers: list[Worker]
    running: bool = False

    download_added = Signal(FileDownload)
    """
    This signal gets emitted when a new download is added to the queue.
    """

    download_finished = Signal(FileDownload)
    """
    This signal gets emitted when a download has finished.
    """

    finished = Signal()
    """
    This signal gets emitted when all worker threads have finished.
    """

    stopped = Signal()
    """
    This signal gets emitted when all worker threads have finished or have been stopped.
    """

    database: TranslationDatabase
    mod_instance: ModInstance
    provider: Provider
    app_config: AppConfig
    user_config: UserConfig
    masterlist: Masterlist

    def __init__(
        self,
        database: TranslationDatabase,
        mod_instance: ModInstance,
        provider: Provider,
        app_config: AppConfig,
        user_config: UserConfig,
        masterlist: Masterlist,
    ) -> None:
        super().__init__()

        self.thread_num = app_config.download_thread_num
        self.queue = Queue()
        self.workers = []

        self.database = database
        self.mod_instance = mod_instance
        self.provider = provider
        self.app_config = app_config
        self.user_config = user_config
        self.masterlist = masterlist

        self.finished.connect(self.stopped.emit)

    def pause(self) -> None:
        """
        Pauses worker threads and blocks code until all threads are paused.
        """

        self.log.info("Pausing worker threads...")

        for worker in self.workers:
            worker.paused = True

        while any(worker.running for worker in self.workers):
            pass

        self.running = False
        self.log.info("Paused worker threads.")

    def resume(self) -> None:
        """
        Unpauses worker threads.
        """

        self.log.info("Continuing worker threads...")
        self.running = True

        for worker in self.workers:
            worker.paused = False

        self.log.info("Continued worker threads.")

    def start(self) -> None:
        """
        Starts worker threads (if not already running).
        """

        if self.running or self.workers:
            return

        self.log.debug(f"Starting {self.thread_num} thread(s)...")

        self.running = True

        self.workers = [
            Worker(
                self.queue,
                i,
                self.app_config,
                self.user_config,
                self.provider,
                self.database,
                self.mod_instance,
            )
            for i in range(self.thread_num)
        ]

        for worker in self.workers:
            worker.task_done.connect(self.__on_worker_finished)
            worker.download_finished.connect(self.download_finished.emit)
            worker.start()

        self.log.info("Threads started, ready for downloads.")

    def __on_worker_finished(self) -> None:
        if (
            self.queue.qsize() == 0
            and all(not worker.processing for worker in self.workers)
            and self.running
        ):
            self.finished.emit()

    def join(self) -> None:
        """
        Blocks code until all mods are processed.
        """

        self.queue.join()

    def terminate(self) -> None:
        """
        Terminates worker threads. **NOT** recommended!
        Use `DownloadManager.stop()` instead, if possible.
        """

        self.log.info("Terminating worker threads...")

        for worker in self.workers:
            worker.terminate()

        self.workers.clear()
        self.stopped.emit()
        self.log.info("Terminated worker threads.")

    def stop(self) -> None:
        """
        Stops worker threads and blocks code until all threads have stopped.
        """

        self.log.info("Stopping worker threads...")

        for worker in self.workers:
            # Terminate paused workers
            if worker.paused or worker.waiting:
                worker.terminate()
            # Or signal them to stop
            else:
                worker.running = False

        while any(worker.isRunning() for worker in self.workers):
            pass

        self.running = False
        self.workers.clear()
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
        self, download: FileDownload, progress_callback: ProgressCallback
    ) -> None:
        """
        Adds a download item to the queue.

        Args:
            download (FileDownload): Download to add.
            progress_callback (ProgressCallback):
                Function or method to call with a ProgressUpdate.
        """

        self.queue.put((download, progress_callback))

    def remove_download_item(self, download: FileDownload) -> None:
        """
        Removes a download item from the queue. This does not cancel it
        if it is already running and just set its `stale` flag to `True`.

        Args:
            download (FileDownload): Download to remove.
        """

        download.stale = True

    def collect_available_downloads(
        self, items: dict[Mod, list[ModFile]], pdialog: Optional[ProgressDialog] = None
    ) -> DownloadListEntries:
        """
        Collects downloads for required translations that are available online.

        Args:
            items (dict[Mod, list[ModFile]]): The items to collect downloads for.
            pdialog (Optional[ProgressDialog], optional):
                Optional Loading dialog. Defaults to None.

        Returns:
            DownloadListEntries:
                Dictionary of mod-file combinations and their downloads.
        """

        self.log.info("Getting downloads for required translations...")

        if pdialog is not None:
            pdialog.updateMainProgress(
                ProgressDialog.UpdatePayload(
                    status_text=self.tr("Collecting available downloads...")
                )
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
            pdialog, max_workers=self.app_config.worker_thread_num
        ) as executor:
            executor.set_main_progress_text(
                self.tr("Collecting available downloads...")
            )

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
                ProgressDialog.UpdatePayload(
                    status_text=f"{mod.name} > {modfile.name} ({m}/{len(modfiles)})",
                    progress_value=m,
                    progress_max=len(modfiles),
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
                    f"Failed to collect downloads for {mod.name!r} > {modfile.name!r}: "
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
            self.provider.get_translations(
                mod.mod_id,
                modfile.name,
                self.user_config.language.id,
                self.masterlist,
                self.user_config.author_blacklist,
            )
        )

        # Use a dict to group translation files from the same mod and source together
        translation_downloads: dict[tuple[int, Source], TranslationDownload] = {}
        for source, translation_ids in available_translations.items():
            for translation_id in translation_ids:
                try:
                    file_details: ModDetails = self.provider.get_details(
                        translation_id, source
                    )
                except Exception as ex:
                    self.log.error(
                        f"Failed to get details for {translation_id}: {ex}",
                        exc_info=ex,
                    )
                    continue

                download = FileDownload(mod_details=file_details, source=source)
                download_id = ModId(
                    mod_id=translation_id.mod_id,
                    nm_id=translation_id.nm_id,
                    nm_game_id=translation_id.nm_game_id,
                )
                translation_name: str = self.provider.get_details(
                    download_id, source=source
                ).display_name
                translation_download = TranslationDownload(
                    mod_info=ModInfo(translation_name, download_id, source),
                    available_downloads=[],
                )
                translation_downloads.setdefault(
                    (download_id.mod_id, source), translation_download
                ).available_downloads.append(download)

        result: list[TranslationDownload] = list(translation_downloads.values())
        return result

    def collect_available_updates(
        self,
        translations: dict[Translation, Mod],
        ldialog: Optional[LoadingDialog] = None,
    ) -> DownloadListEntries:
        """
        Collects available updates for the installed translations.

        Args:
            translations (dict[Translation, Mod]):
                Map of installed translations that have an available update
                and their original mod.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            DownloadListEntries: Entries for the download list dialog.
        """

        self.log.info(
            f"Collecting available updates for {len(translations)} translation(s)..."
        )

        downloads: DownloadListEntries = {}
        for t, (translation, original_mod) in enumerate(translations.items()):
            if ldialog is not None:
                ldialog.updateProgress(
                    text1=self.tr("Collecting available translation updates...")
                    + f" ({t}/{len(translations)})",
                    value1=t,
                    max1=len(translations),
                    show2=True,
                    text2=translation.name,
                    value2=0,
                    max2=0,
                )

            downloads.update(
                self.__collect_update_for_translation(translation, original_mod)
            )

        return downloads

    def __collect_update_for_translation(
        self, translation: Translation, original_mod: Mod
    ) -> DownloadListEntries:
        if translation.mod_id is None:
            return {}

        new_file_id: Optional[ModId] = self.provider.get_updated_mod_id(
            translation.mod_id
        )

        mod_info = ModInfo(translation.name, translation.mod_id, translation.source)

        if new_file_id is None:
            return {}

        downloads: DownloadListEntries = {}

        for modfile in translation.strings:
            downloads.setdefault(mod_info, {})[modfile] = [
                TranslationDownload(
                    mod_info=mod_info,
                    available_downloads=[
                        FileDownload(
                            mod_details=self.provider.get_details(new_file_id),
                            source=translation.source,
                        )
                    ],
                )
            ]

        return downloads
