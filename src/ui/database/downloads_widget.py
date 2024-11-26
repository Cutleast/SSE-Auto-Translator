"""
This file is part of SEE Auto Translator
and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import time
import traceback
import urllib.parse
from enum import Enum, auto
from pathlib import Path
from queue import Queue

from PySide6.QtCore import QEventLoop, Qt, QTimerEvent, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QMessageBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app import MainApp
from core.database.translation import Translation
from core.translation_provider.downloader import Downloader
from core.translation_provider.file_download import FileDownload
from core.utilities import apply_dark_title_bar, clean_fs_name, scale_value
from core.utilities.importer import import_from_archive, import_non_plugin_files
from core.utilities.source import Source
from core.utilities.thread import Thread
from ui.widgets.progress_widget import ProgressWidget
from ui.widgets.toast import Toast


class DownloadsWidget(QWidget):
    """
    Widget for Downloads.
    """

    queue: Queue = None
    thread: Thread = None
    downloader: Downloader = None

    pending_non_prem_downloads: dict[tuple[int, int], FileDownload] = {}

    current_download: FileDownload | None = None

    download_finished = Signal()
    queue_finished = Signal()
    update_signal = Signal(tuple)

    hide_item_signal = Signal(QTreeWidgetItem)

    start_timer_signal = Signal()
    stop_timer_signal = Signal()

    timer_id: int | None = None

    class Status(Enum):
        Running = auto()
        Paused = auto()
        Stopped = auto()

    status: Status = Status.Running

    log = logging.getLogger("Downloader")

    def __init__(self, app: MainApp):
        super().__init__()

        self.app = app
        self.loc = app.loc
        self.mloc = app.loc.database

        self.update_signal.connect(
            self._update_progress, Qt.ConnectionType.QueuedConnection
        )
        self.hide_item_signal.connect(
            self._hide_item, Qt.ConnectionType.QueuedConnection
        )
        self.start_timer_signal.connect(self.start_timer)
        self.stop_timer_signal.connect(self.stop_timer)

        self.queue = Queue()
        self.downloader = Downloader()
        self.thread = Thread(self.download_thread)
        self.thread.start()

        self.toast = Toast(self.loc.main.download_started, parent=self.app.root)
        self.toast.setIcon(self.app.windowIcon())

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        self.downloads_widget = QTreeWidget()
        self.downloads_widget.setObjectName("download_list")
        self.downloads_widget.setAlternatingRowColors(True)
        self.downloads_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        vlayout.addWidget(self.downloads_widget)

        self.downloads_widget.setHeaderLabels(
            [
                self.mloc.translation_name,
                self.loc.main.status,
            ]
        )

        self.downloads_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )
        self.downloads_widget.header().setStretchLastSection(False)
        self.downloads_widget.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )

    def showEvent(self, event):
        super().showEvent(event)

        self.downloads_widget.header().resizeSection(1, 400)

    def start_timer(self):
        if self.timer_id is None:
            self.timer_id = self.startTimer(1000, Qt.TimerType.PreciseTimer)

    def stop_timer(self):
        if self.timer_id is not None:
            self.killTimer(self.timer_id)
            self.timer_id = None

    def timerEvent(self, event: QTimerEvent):
        super().timerEvent(event)

        self._update_progress((None, None))

    def update_progress(self, download_data: tuple[FileDownload, FileDownload.Status]):
        self.update_signal.emit(download_data)

    def _update_progress(
        self, download_data: tuple[FileDownload | None, FileDownload.Status | None]
    ):
        """
        Updates progress of current downloading translation.
        """

        download, status = download_data

        if download is None:
            download = self.current_download

        if download:
            item = download.tree_item
            if item is None:
                return

            if self.downloads_widget.itemWidget(item, 1) is None:
                item.setText(1, "")
                progress_widget = ProgressWidget(item)
                progress_widget.progress_bar.setRange(0, 1000)
                self.downloads_widget.setItemWidget(item, 1, progress_widget)

            progress_widget: ProgressWidget = self.downloads_widget.itemWidget(item, 1)

            if status is None:
                status = download.status

            match status:
                case FileDownload.Status.Downloading:
                    if self.downloader.current_size and self.downloader.previous_size:
                        cur_size = scale_value(self.downloader.current_size)
                        tot_size = scale_value(self.downloader.file_size)
                        progress_widget.progress_bar.setRange(0, 1000)
                        progress_widget.progress_bar.setValue(
                            int(
                                (
                                    self.downloader.current_size
                                    / self.downloader.file_size
                                )
                                * 1000
                            )
                        )
                        spd = (
                            self.downloader.current_size - self.downloader.previous_size
                        )
                        cur_speed = scale_value(spd) + "/s"
                        percentage = f"{(self.downloader.current_size / self.downloader.file_size * 100):.2f} %"
                        status_text = f"{self.loc.main.downloading} ({cur_size}/{tot_size} - {percentage} - {cur_speed})"
                    else:
                        status_text = self.loc.main.downloading

                    self.downloader.previous_size = self.downloader.current_size

                    progress_widget.status_label.setText(status_text)
                case FileDownload.Status.Processing:
                    progress_widget.status_label.setText(self.loc.main.processing)
                    progress_widget.progress_bar.setRange(0, 0)
                case FileDownload.Status.DownloadFailed:
                    progress_widget.status_label.setText(self.loc.main.download_failed)
                    progress_widget.progress_bar.hide()
                case FileDownload.Status.DownloadSuccess:
                    item.setHidden(True)

        self.app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents)

    @staticmethod
    def _hide_item(item: QTreeWidgetItem):
        item.setHidden(True)

    def download_thread(self):
        """
        Thread to download items from queue.
        """

        self.log.debug("Thread started.")

        while self.status == self.Status.Running:
            download: FileDownload = self.queue.get()
            self.current_download = download
            download.status = download.Status.Processing
            self.update_progress((download, download.Status.Processing))

            tmp_path = self.app.get_tmp_dir()
            dl_path = (
                Path(self.app.app_config["downloads_path"] or self.app.get_tmp_dir())
            )

            self.log.info(
                f"Downloading file {download.file_name!r} from {download.direct_url!r}..."
            )

            downloaded_file = dl_path / download.file_name
            download.status = download.Status.Downloading
            self.update_progress((download, download.Status.Downloading))

            progress_widget: ProgressWidget
            while (
                progress_widget := self.downloads_widget.itemWidget(
                    download.tree_item, 1
                )
            ) is None:
                self.update_progress((download, download.Status.Downloading))
                time.sleep(0.1)

            self.start_timer_signal.emit()
            if not downloaded_file.is_file():
                try:
                    self.downloader.download(download, dl_path)
                except Exception as ex:
                    self.log.error(f"Download failed: {ex}", exc_info=ex)
                    download.status = download.Status.DownloadFailed
                    progress_widget.set_exception(
                        "".join(traceback.format_exception(ex))
                    )
                    self.update_progress((download, download.Status.DownloadFailed))

            self.stop_timer_signal.emit()

            if downloaded_file.is_file():
                self.log.debug(f"Processing file...")
                download.status = download.Status.Processing
                self.update_progress((download, download.Status.Processing))
                try:
                    strings = import_from_archive(
                        downloaded_file,
                        self.app.mainpage_widget.mods,
                        tmp_path,
                        self.app.cacher,
                    )
                except Exception as ex:
                    self.log.error(
                        f"Failed to import translation from downloaded archive: {ex}",
                        exc_info=ex,
                    )
                    download.status = download.Status.DownloadFailed
                    self.update_progress((download, download.Status.DownloadFailed))
                    progress_widget.set_exception(
                        "".join(traceback.format_exception(ex))
                    )

                else:
                    if download.original_mod is None and strings:
                        plugin_name = list(strings.keys())[0].lower()

                        for mod in self.app.mainpage_widget.mods:
                            if any(
                                plugin_name == plugin.name.lower()
                                for plugin in mod.plugins
                            ):
                                download.original_mod = mod

                    if strings:
                        translation_details = self.app.provider.get_details(
                            mod_id=download.mod_id,
                            file_id=download.file_id,
                            source=download.source,
                        )
                        translation = Translation(
                            download.name,
                            download.mod_id,
                            download.file_id,
                            translation_details["version"],
                            download.original_mod.mod_id,
                            download.original_mod.file_id,
                            download.original_mod.version,
                            self.app.database.userdb_path
                            / self.app.database.language
                            / download.name,
                            strings=strings,
                            status=Translation.Status.Ok,
                            source=download.source,
                            timestamp=translation_details["timestamp"],
                        )
                        translation.save_translation()
                        self.app.database.add_translation(translation)

                        import_non_plugin_files(
                            downloaded_file,
                            download.original_mod,
                            translation,
                            self.app.get_tmp_dir(),
                            self.app.user_config,
                        )

                        download.status = download.Status.DownloadSuccess
                        self.update_progress(
                            (download, download.Status.DownloadSuccess)
                        )

                        self.log.info("Processing complete.")
                    else:
                        self.log.warning("Translation does not contain any strings!")
                        download.status = download.Status.DownloadFailed
                        progress_widget.set_exception(
                            "Merging failed! Translation does not contain any matching strings!"
                        )
                        self.update_progress((download, download.Status.DownloadFailed))

                self.download_finished.emit()
            else:
                self.log.error("Download failed: File could not be downloaded!")
                download.status = download.Status.DownloadFailed
                progress_widget.set_exception("File could not be downloaded!")
                self.update_progress((download, download.Status.DownloadFailed))

            self.current_download = None
            self.queue.task_done()

            if self.queue.empty() and not self.pending_non_prem_downloads:
                self.queue_finished.emit()

        self.log.debug("Thread stopped.")

    def add_download(self, nxm_url: str):
        """
        Starts download from `nxm_url` (nxm://...).

        Example URL:
            `nxm://skyrimspecialedition/mods/100260/files/464417?key=FpPPz6z3ZKdD71vtmLHD_A&expires=1708262728&user_id=65733731`
        """

        scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(nxm_url)

        path_parts = Path(path).parts
        mod_id = int(path_parts[2])
        file_id = int(path_parts[4])
        source = Source.NexusMods

        parsed_query = urllib.parse.parse_qs(query)

        (key,) = parsed_query["key"]
        (expires,) = parsed_query["expires"]
        (user_id,) = parsed_query["user_id"]

        installed_translation = self.app.database.get_translation_by_id(mod_id)

        if installed_translation:
            if installed_translation.file_id == file_id:
                mb = QMessageBox(self.app.root)
                mb.setWindowTitle(self.mloc.already_installed)
                mb.setText(self.mloc.already_installed_text)
                apply_dark_title_bar(mb)
                mb.setStandardButtons(mb.StandardButton.Ok)
                mb.exec()

                return

        if (mod_id, file_id) not in self.pending_non_prem_downloads:
            mod_details = self.app.provider.get_details(mod_id, file_id, source)
            download = FileDownload(
                name=clean_fs_name(mod_details["name"]),
                source=source,
                mod_id=mod_id,
                file_id=file_id,
                file_name=mod_details["filename"],
                direct_url=self.app.provider.get_direct_download_url(
                    mod_id, file_id, key, int(expires)
                ),
            )

            item = QTreeWidgetItem(
                [
                    download.name,
                    self.loc.main.waiting_for_download,
                ]
            )
            item.setIcon(
                0, QIcon(str(self.app.res_path / "icons" / "nexus_mods.svg"))
            )
            item.setFont(1, QFont("Consolas"))
            download.tree_item = item
            self.downloads_widget.addTopLevelItem(item)
        else:
            download = self.pending_non_prem_downloads.pop((mod_id, file_id))
            download.direct_url = self.app.provider.get_direct_download_url(
                mod_id, file_id, key, int(expires)
            )
            self.downloads_widget.itemWidget(download.tree_item, 1).hide()
            self.downloads_widget.removeItemWidget(download.tree_item, 1)
            download.tree_item.setText(1, self.loc.main.waiting_for_download)

        self.queue.put(download)

        self.app.mainpage_widget.database_widget.setCurrentIndex(1)
        self.toast.show()

    def all_finished(self):
        """
        Shows messagebox to tell that all downloads in queue are finished.
        """

        # Remove hidden (finished) items from download list
        visible_items = False
        for index in range(self.downloads_widget.topLevelItemCount()):
            item = self.downloads_widget.topLevelItem(index)
            if item is None:
                continue
            if item.isHidden():
                self.downloads_widget.takeTopLevelItem(index)
            else:
                visible_items = True

        messagebox = QMessageBox(self.app.root)
        messagebox.setWindowTitle(self.loc.main.success)
        messagebox.setText(self.mloc.queue_finished)
        apply_dark_title_bar(messagebox)
        messagebox.exec()

        # Only switch to translations tab if there are no download items left
        if not visible_items:
            self.app.mainpage_widget.database_widget.setCurrentIndex(0)

        self.queue_finished.disconnect(self.all_finished)
