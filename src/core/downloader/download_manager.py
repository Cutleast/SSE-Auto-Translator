"""
Copyright (c) Cutleast
"""

import logging
from queue import Queue
from typing import Optional

from PySide6.QtCore import QObject, Signal

from app_context import AppContext
from core.config.user_config import UserConfig
from core.mod_instance.mod import Mod
from core.mod_instance.plugin import Plugin
from core.translation_provider.provider import Provider
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

    def __init__(self) -> None:
        super().__init__()

        self.queue = Queue()
        self.workers = []

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
            Worker(self.queue, i) for i in range(DownloadManager.THREAD_NUM)
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
        self, items: dict[Mod, list[Plugin]], ldialog: Optional[LoadingDialog] = None
    ) -> dict[str, list[TranslationDownload]]:
        """
        Collects downloads for required translations that are available online.

        Args:
            items (dict[Mod, list[Plugin]]): The items to collect downloads for.
            ldialog (Optional[LoadingDialog], optional):
                Optional Loading dialog. Defaults to None.

        Returns:
            dict[str, list[TranslationDownload]]:
                Dictionary of mod-plugin combinations and their downloads.
        """

        self.log.info("Getting downloads for required translations...")

        provider: Provider = AppContext.get_app().provider

        if ldialog is not None:
            ldialog.updateProgress(text1=self.tr("Collecting available downloads..."))

        # Filter items for plugins that have an available translation
        items = {
            mod: [
                plugin
                for plugin in plugins
                if plugin.status == Plugin.Status.TranslationAvailableOnline
            ]
            for mod, plugins in items.items()
        }
        items = {mod: plugins for mod, plugins in items.items() if plugins}

        translation_downloads: dict[str, list[TranslationDownload]] = {}
        for m, (mod, plugins) in enumerate(items.items()):
            if ldialog is not None:
                ldialog.updateProgress(
                    text1=self.tr("Collecting available downloads...")
                    + f" ({m}/{len(items)})",
                    value1=m,
                    max1=len(items),
                )

            download_units: dict[str, list[TranslationDownload]] = (
                self.__collect_downloads_for_mod(mod, plugins, ldialog)
            )

            for name, downloads in download_units.items():
                if downloads:
                    translation_downloads.setdefault(name, []).extend(downloads)

        # Sort translation downloads in descending order
        # after last updated/uploaded timestamp
        translation_downloads = {
            display_name: downloads
            for display_name, downloads in sorted(
                translation_downloads.copy().items(),
                key=lambda item: provider.get_details(
                    item[1][0].mod_id, source=item[1][0].source
                )["timestamp"],
            )
        }

        return translation_downloads

    def __collect_downloads_for_mod(
        self, mod: Mod, plugins: list[Plugin], ldialog: Optional[LoadingDialog] = None
    ) -> dict[str, list[TranslationDownload]]:
        download_units: dict[str, list[TranslationDownload]] = {}
        for p, plugin in enumerate(plugins):
            if ldialog is not None:
                ldialog.updateProgress(
                    show2=True,
                    text2=f"{mod.name} > {plugin.name} ({p}/{len(plugins)})",
                    value2=p,
                    max2=len(plugins),
                )

            plugin_downloads: list[TranslationDownload] = (
                self.__collect_downloads_for_plugin(mod, plugin, ldialog)
            )
            if plugin_downloads:
                download_units[f"{mod.name} > {plugin.name}"] = plugin_downloads

        return download_units

    def __collect_downloads_for_plugin(
        self, mod: Mod, plugin: Plugin, ldialog: Optional[LoadingDialog] = None
    ) -> list[TranslationDownload]:
        provider: Provider = AppContext.get_app().provider
        user_config: UserConfig = AppContext.get_app().user_config

        translation_downloads: list[TranslationDownload] = []
        available_translations: list[tuple[int, list[int], Source]] = (
            provider.get_translations(
                mod.mod_id,
                plugin.name,
                user_config.language,
                user_config.author_blacklist,
            )
        )

        for mod_id, file_ids, source in available_translations:
            downloads: list[FileDownload] = []

            if source == Source.NexusMods:
                for file_id in file_ids:
                    try:
                        file_details = provider.get_details(mod_id, file_id, source)
                    except Exception as ex:
                        self.log.error(
                            f"Failed to get details for {mod_id} > {file_id}: {ex}",
                            exc_info=ex,
                        )
                        continue

                    download = FileDownload(
                        display_name=clean_fs_name(file_details["name"]),
                        source=source,
                        mod_id=mod_id,
                        file_id=file_id,
                        original_mod=mod,
                        file_name=file_details["filename"],
                    )
                    downloads.append(download)

            else:
                try:
                    file_details = provider.get_details(mod_id, source=source)
                except Exception as ex:
                    self.log.error(
                        f"Failed to get details for {mod_id}: {ex}",
                        exc_info=ex,
                    )
                    continue

                download = FileDownload(
                    display_name=clean_fs_name(file_details["name"]),
                    source=source,
                    mod_id=mod_id,
                    original_mod=mod,
                    file_name=file_details["filename"],
                )
                downloads.append(download)

            if not downloads:
                continue

            translation_name: str = provider.get_details(mod_id, source=source).get(
                "name", f"{mod.name} - {user_config.language}"
            )
            translation_download = TranslationDownload(
                name=translation_name,
                mod_id=mod_id,
                original_mod=mod,
                plugin_name=plugin.name,
                source=source,
                available_downloads=downloads,
            )
            translation_downloads.append(translation_download)

        translation_downloads.sort(
            key=lambda download: provider.get_details(
                download.mod_id, source=download.source
            )["timestamp"],
            reverse=True,
        )

        return translation_downloads
