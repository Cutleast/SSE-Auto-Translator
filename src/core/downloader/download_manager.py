"""
Copyright (c) Cutleast
"""

import logging
from queue import Queue
from typing import Optional

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
from core.utilities.filesystem import clean_fs_name
from core.utilities.progress_update import ProgressCallback
from ui.widgets.loading_dialog import LoadingDialog

from .file_download import FileDownload
from .translation_download import TranslationDownload
from .worker import Worker


class DownloadManager(QObject):
    """
    Class for managing and running downloads and installations of translations.
    """

    log: logging.Logger = logging.getLogger("DownloadManager")

    THREAD_NUM: int = 1  # TODO: Make this configurable by the user

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

        self.log.debug(f"Starting {DownloadManager.THREAD_NUM} thread(s)...")

        self.running = True

        self.workers = [
            Worker(
                self.queue,
                i,
                self.app_config,
                self.provider,
                self.database,
                self.mod_instance,
            )
            for i in range(DownloadManager.THREAD_NUM)
        ]

        for worker in self.workers:
            worker.finished.connect(self.__on_worker_finished)
            worker.download_finished.connect(self.download_finished.emit)
            worker.start()

        self.log.info("Threads started, ready for downloads.")

    def __on_worker_finished(self) -> None:
        if all(worker.isFinished() for worker in self.workers) and self.running:
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
        self, items: dict[Mod, list[ModFile]], ldialog: Optional[LoadingDialog] = None
    ) -> dict[tuple[str, ModId], list[TranslationDownload]]:
        """
        Collects downloads for required translations that are available online.

        Args:
            items (dict[Mod, list[ModFile]]): The items to collect downloads for.
            ldialog (Optional[LoadingDialog], optional):
                Optional Loading dialog. Defaults to None.

        Returns:
            dict[tuple[str, ModId], list[TranslationDownload]]:
                Dictionary of mod-file combinations and their downloads.
        """

        self.log.info("Getting downloads for required translations...")

        if ldialog is not None:
            ldialog.updateProgress(text1=self.tr("Collecting available downloads..."))

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

        translation_downloads: dict[tuple[str, ModId], list[TranslationDownload]] = {}
        for m, (mod, modfiles) in enumerate(items.items()):
            if ldialog is not None:
                ldialog.updateProgress(
                    text1=self.tr("Collecting available downloads...")
                    + f" ({m}/{len(items)})",
                    value1=m,
                    max1=len(items),
                )

            download_units: dict[str, list[TranslationDownload]] = (
                self.__collect_downloads_for_mod(mod, modfiles, ldialog)
            )

            for name, downloads in download_units.items():
                if downloads:
                    translation_downloads.setdefault((name, mod.mod_id), []).extend(
                        downloads
                    )

        # Sort translation downloads in descending order
        # after last updated/uploaded timestamp
        translation_downloads = {
            index: downloads
            for index, downloads in sorted(
                translation_downloads.copy().items(),
                key=lambda item: self.provider.get_details(
                    item[1][0].mod_id, source=item[1][0].source
                ).timestamp,
            )
        }

        return translation_downloads

    def __collect_downloads_for_mod(
        self, mod: Mod, modfiles: list[ModFile], ldialog: Optional[LoadingDialog] = None
    ) -> dict[str, list[TranslationDownload]]:
        download_units: dict[str, list[TranslationDownload]] = {}
        for m, modfile in enumerate(modfiles):
            if ldialog is not None:
                ldialog.updateProgress(
                    show2=True,
                    text2=f"{mod.name} > {modfile.name} ({m}/{len(modfiles)})",
                    value2=m,
                    max2=len(modfiles),
                )

            try:
                modfile_downloads: list[TranslationDownload] = (
                    self.__collect_downloads_for_modfile(mod, modfile, ldialog)
                )
                if modfile_downloads:
                    download_units[f"{mod.name} > {modfile.name}"] = modfile_downloads
            except Exception as ex:
                self.log.error(
                    f"Failed to collect downloads for {mod.name!r} > {modfile.name!r}: "
                    + str(ex),
                    exc_info=ex,
                )

        return download_units

    def __collect_downloads_for_modfile(
        self, mod: Mod, modfile: ModFile, ldialog: Optional[LoadingDialog] = None
    ) -> list[TranslationDownload]:
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

                download = FileDownload(
                    display_name=clean_fs_name(file_details.display_name),
                    source=source,
                    mod_id=translation_id,
                    file_name=file_details.file_name,
                )

                download_id = ModId(
                    mod_id=translation_id.mod_id,
                    nm_id=translation_id.nm_id,
                    nm_game_id=translation_id.nm_game_id,
                )
                translation_name: str = self.provider.get_details(
                    download_id, source=source
                ).display_name
                translation_download = TranslationDownload(
                    name=translation_name,
                    mod_id=download_id,
                    modfile_name=modfile.name,
                    source=source,
                    available_downloads=[],
                )
                translation_downloads.setdefault(
                    (download_id.mod_id, source), translation_download
                ).available_downloads.append(download)

        result: list[TranslationDownload] = list(translation_downloads.values())

        # Sort after upload timestamp so that newest translations are first
        result.sort(
            key=lambda download: self.provider.get_details(
                download.mod_id, source=download.source
            ).timestamp,
            reverse=True,
        )

        return result

    def collect_available_updates(
        self,
        translations: dict[Translation, Mod],
        ldialog: Optional[LoadingDialog] = None,
    ) -> dict[tuple[str, ModId], list[TranslationDownload]]:
        """
        Collects available updates for the installed translations.

        Args:
            translations (dict[Translation, Mod]):
                Map of installed translations that have an available update
                and their original mod.
            ldialog (Optional[LoadingDialog], optional):
                Optional loading dialog. Defaults to None.

        Returns:
            dict[tuple[str, ModId], list[TranslationDownload]]:
                Dictionary of mod-file combinations and their downloads.
        """

        self.log.info(
            f"Collecting available updates for {len(translations)} translation(s)..."
        )

        downloads: dict[tuple[str, ModId], list[TranslationDownload]] = {}
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
    ) -> dict[tuple[str, ModId], list[TranslationDownload]]:
        if translation.mod_id is None:
            return {}

        new_file_id: Optional[ModId] = self.provider.get_updated_mod_id(
            translation.mod_id
        )

        if new_file_id is None:
            return {}

        downloads: dict[tuple[str, ModId], list[TranslationDownload]] = {}

        for modfile_name in translation.strings:
            downloads[f"{translation.name} > {modfile_name}", translation.mod_id] = [
                TranslationDownload(
                    name=translation.name,
                    mod_id=translation.mod_id,
                    modfile_name=modfile_name,
                    source=Source.NexusMods,  # TODO: Reimplement translation updates from CDT
                    available_downloads=[
                        FileDownload(
                            display_name=translation.name,
                            source=Source.NexusMods,
                            mod_id=translation.mod_id,
                            file_name=self.provider.get_details(
                                new_file_id, Source.NexusMods
                            ).file_name,
                        )
                    ],
                )
            ]

        return downloads
