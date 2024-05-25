"""
This file is part of SEE Auto Translator
and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import urllib.parse
from enum import Enum, auto
from pathlib import Path
from queue import Queue

import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import qtpy.QtWidgets as qtw

import utilities as utils
from main import MainApp
from translation_provider import FileDownload, Downloader
from widgets import ProgressWidget

from .translation import Translation


class DownloadsWidget(qtw.QWidget):
    """
    Widget for Downloads.
    """

    queue: Queue = None
    thread: utils.Thread = None
    downloader: Downloader = None

    pending_non_prem_downloads: dict[tuple[int, int], FileDownload] = {}

    current_download: FileDownload | None = None

    download_finished = qtc.Signal()
    queue_finished = qtc.Signal()
    update_signal = qtc.Signal()

    hide_item_signal = qtc.Signal(qtw.QTreeWidgetItem)

    start_timer_signal = qtc.Signal()
    stop_timer_signal = qtc.Signal()

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

        self.update_signal.connect(self._update_progress)
        self.hide_item_signal.connect(self._hide_item)
        self.start_timer_signal.connect(self.start_timer)
        self.stop_timer_signal.connect(self.stop_timer)

        self.queue = Queue()
        self.downloader = Downloader()
        self.thread = utils.Thread(self.download_thread)
        self.thread.start()

        vlayout = qtw.QVBoxLayout()
        self.setLayout(vlayout)

        self.downloads_widget = qtw.QTreeWidget()
        self.downloads_widget.setObjectName("download_list")
        self.downloads_widget.setAlternatingRowColors(True)
        self.downloads_widget.setFocusPolicy(qtc.Qt.FocusPolicy.NoFocus)
        vlayout.addWidget(self.downloads_widget)

        self.downloads_widget.setHeaderLabels(
            [
                self.mloc.translation_name,
                self.loc.main.status,
            ]
        )

        self.downloads_widget.setSelectionMode(
            qtw.QAbstractItemView.SelectionMode.NoSelection
        )
        self.downloads_widget.header().setStretchLastSection(False)
        self.downloads_widget.header().setSectionResizeMode(
            0, qtw.QHeaderView.ResizeMode.Stretch
        )

    def showEvent(self, event):
        super().showEvent(event)

        self.downloads_widget.header().resizeSection(1, 400)

    def start_timer(self):
        if self.timer_id is None:
            self.timer_id = self.startTimer(1000, qtc.Qt.TimerType.PreciseTimer)

    def stop_timer(self):
        if self.timer_id is not None:
            self.killTimer(self.timer_id)
            self.timer_id = None

    def timerEvent(self, event: qtc.QTimerEvent):
        super().timerEvent(event)

        self._update_progress()

    def update_progress(self):
        self.update_signal.emit()

    def _update_progress(self):
        """
        Updates progress of current downloading translation.
        """

        if self.current_download:
            item = self.current_download.tree_item
            if item is None:
                return

            if self.downloads_widget.itemWidget(item, 1) is None:
                item.setText(1, "")
                progress_widget = ProgressWidget()
                progress_widget.progress_bar.setRange(0, 1000)
                self.downloads_widget.setItemWidget(item, 1, progress_widget)

            progress_widget: ProgressWidget = self.downloads_widget.itemWidget(item, 1)

            match self.current_download.status:
                case FileDownload.Status.Downloading:
                    if self.downloader.current_size and self.downloader.previous_size:
                        cur_size = utils.scale_value(self.downloader.current_size)
                        tot_size = utils.scale_value(self.downloader.file_size)
                        progress_widget.progress_bar.setValue(
                            (self.downloader.current_size / self.downloader.file_size)
                            * 1000
                        )
                        spd = (
                            self.downloader.current_size - self.downloader.previous_size
                        )
                        cur_speed = utils.scale_value(spd) + "/s"
                        percentage = f"{(self.downloader.current_size / self.downloader.file_size * 100):.2f} %"
                        status = f"{self.loc.main.downloading} ({cur_size}/{tot_size} - {percentage} - {cur_speed})"
                    else:
                        status = self.loc.main.downloading

                    self.downloader.previous_size = self.downloader.current_size

                    progress_widget.status_label.setText(status)
                case FileDownload.Status.Processing:
                    progress_widget.status_label.setText(self.loc.main.processing)
                    progress_widget.progress_bar.setRange(0, 0)
                case FileDownload.Status.DownloadFailed:
                    progress_widget.status_label.setText(self.loc.main.download_failed)
                    progress_widget.progress_bar.hide()
                case FileDownload.Status.DownloadSuccess:
                    item.setHidden(True)

        self.update()

    @staticmethod
    def _hide_item(item: qtw.QTreeWidgetItem):
        item.setHidden(True)

    def download_thread(self):
        """
        Thread to download items from queue.
        """

        self.app.log.debug("Thread started.")

        while self.status == self.Status.Running:
            download: FileDownload = self.queue.get()
            self.current_download = download
            download.status = download.Status.Processing
            self.update_progress()

            tmp_path = self.app.get_tmp_dir()

            self.app.log.info(
                f"Downloading file {download.file_name!r} from {download.direct_url!r}..."
            )

            downloaded_file = tmp_path / download.file_name
            download.status = download.Status.Downloading

            self.start_timer_signal.emit()
            if not downloaded_file.is_file():
                self.downloader.download(download, tmp_path)
            self.stop_timer_signal.emit()

            if downloaded_file.is_file():
                self.app.log.debug(f"Processing file...")
                download.status = download.Status.Processing
                self.update_progress()
                try:
                    strings = utils.import_from_archive(
                        downloaded_file,
                        self.app.mainpage_widget.mods,
                        self.app.get_tmp_dir(),
                    )
                except Exception as ex:
                    self.log.error(
                        f"Failed to import translation from downloaded archive: {ex}",
                        exc_info=ex,
                    )
                    download.status = download.Status.DownloadFailed

                else:
                    if download.original_mod is None:
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

                        utils.import_non_plugin_files(
                            downloaded_file,
                            download.original_mod,
                            translation,
                            self.app.get_tmp_dir(),
                            self.app.user_config,
                        )

                        download.status = download.Status.DownloadSuccess
                        self.hide_item_signal.emit(download.tree_item)

                        self.app.log.info("Processing complete.")
                    else:
                        self.app.log.warning(
                            "Translation does not contain any strings!"
                        )
                        download.status = download.Status.DownloadFailed

                self.download_finished.emit()

            else:
                self.app.log.error("Download failed!")
                download.status = download.Status.DownloadFailed

            self.update_progress()
            self.current_download = None
            self.queue.task_done()

            if self.queue.empty() and not self.pending_non_prem_downloads:
                self.queue_finished.emit()

        self.app.log.debug("Thread stopped.")

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
        source = utils.Source.NexusMods

        parsed_query = urllib.parse.parse_qs(query)

        (key,) = parsed_query["key"]
        (expires,) = parsed_query["expires"]
        (user_id,) = parsed_query["user_id"]

        installed_translation = self.app.database.get_translation_by_id(mod_id)

        if installed_translation:
            if installed_translation.file_id == file_id:
                mb = qtw.QMessageBox(self.app.root)
                mb.setWindowTitle(self.mloc.already_installed)
                mb.setText(self.mloc.already_installed_text)
                utils.apply_dark_title_bar(mb)
                mb.setStandardButtons(mb.StandardButton.Ok)
                mb.exec()

                return

        if (mod_id, file_id) not in self.pending_non_prem_downloads:
            mod_details = self.app.provider.get_details(mod_id, file_id, source)
            download = FileDownload(
                name=mod_details["name"],
                source=source,
                mod_id=mod_id,
                file_id=file_id,
                file_name=mod_details["filename"],
                direct_url=self.app.provider.get_direct_download_url(
                    mod_id, file_id, key, int(expires)
                ),
            )

            item = qtw.QTreeWidgetItem(
                [
                    download.name,
                    self.loc.main.waiting_for_download,
                ]
            )
            item.setIcon(
                0, qtg.QIcon(str(self.app.data_path / "icons" / "nexus_mods.svg"))
            )
            item.setFont(1, qtg.QFont("Consolas"))
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

    def all_finished(self):
        """
        Shows messagebox to tell that all downloads in queue are finished.
        """

        self.app.database.save_database()

        self.downloads_widget.clear()

        messagebox = qtw.QMessageBox(self.app.root)
        messagebox.setWindowTitle(self.loc.main.success)
        messagebox.setText(self.mloc.queue_finished)
        utils.apply_dark_title_bar(messagebox)
        messagebox.exec()

        self.app.mainpage_widget.database_widget.setCurrentIndex(0)

        self.queue_finished.disconnect(self.all_finished)
