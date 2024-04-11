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
from nm_api import Download, Downloader
from widgets import ProgressWidget

from .translation import Translation


class DownloadsWidget(qtw.QWidget):
    """
    Widget for Downloads.
    """

    queue: Queue = None
    downloader: Downloader = None
    thread: utils.Thread = None

    download_finished = qtc.Signal()
    queue_finished = qtc.Signal()
    update_signal = qtc.Signal()

    start_timer_signal = qtc.Signal()
    stop_timer_signal = qtc.Signal()

    timer_id: int | None = None

    class Status(Enum):
        Running = auto()
        Paused = auto()
        Stopped = auto()

    current_translation: Translation = None
    current_download: Download = None

    status: Status = Status.Running

    items: dict[Translation, qtw.QTreeWidgetItem] = {}

    log = logging.getLogger("Downloader")

    def __init__(self, app: MainApp):
        super().__init__()

        self.app = app
        self.loc = app.loc
        self.mloc = app.loc.database

        self.update_signal.connect(self._update_progress)
        self.start_timer_signal.connect(self.start_timer)
        self.stop_timer_signal.connect(self.stop_timer)

        self.queue = Queue()
        self.downloader = Downloader(self.app.api, "skyrimspecialedition")
        self.thread = utils.Thread(self.download_thread)
        self.thread.start()

        vlayout = qtw.QVBoxLayout()
        self.setLayout(vlayout)

        self.downloads_widget = qtw.QTreeWidget()
        self.downloads_widget.setObjectName("download_list")
        self.downloads_widget.setAlternatingRowColors(True)
        # self.downloads_widget.setUniformRowHeights(False)
        vlayout.addWidget(self.downloads_widget)

        self.downloads_widget.setHeaderLabels(
            [
                self.mloc.translation_name,
                self.loc.main.status,
            ]
        )

        self.downloads_widget.setSelectionMode(
            qtw.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.downloads_widget.header().setStretchLastSection(False)
        self.downloads_widget.header().setSectionResizeMode(
            qtw.QHeaderView.ResizeMode.Stretch
        )

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

        if self.current_download and self.current_translation:
            item = self.items.get(self.current_translation)
            if item is None:
                return

            if self.downloads_widget.itemWidget(item, 1) is None:
                item.setText(1, "")
                progress_widget = ProgressWidget()
                self.downloads_widget.setItemWidget(item, 1, progress_widget)
                # item.setSizeHint(1, qtc.QSize(item.sizeHint(1).width(), progress_widget.sizeHint().height()))

            progress_widget: ProgressWidget = self.downloads_widget.itemWidget(item, 1)

            match self.current_translation.status:
                case Translation.Status.Downloading:
                    if (
                        self.current_download.current_size
                        and self.current_download.previous_size
                    ):
                        cur_size = utils.scale_value(self.current_download.current_size)
                        tot_size = utils.scale_value(self.current_download.file_size)
                        progress_widget.progress_bar.setMaximum(
                            self.current_download.file_size
                        )
                        progress_widget.progress_bar.setValue(
                            self.current_download.current_size
                        )
                        spd = (
                            self.current_download.current_size
                            - self.current_download.previous_size
                        )
                        cur_speed = utils.scale_value(spd) + "/s"
                        percentage = f"{(self.current_download.current_size / self.current_download.file_size * 100):.2f} %"
                        status = f"{self.loc.main.downloading} ({cur_size}/{tot_size} - {percentage} - {cur_speed})"
                    else:
                        status = self.loc.main.downloading

                    self.current_download.previous_size = (
                        self.current_download.current_size
                    )

                    progress_widget.status_label.setText(status)
                case Translation.Status.Processing:
                    progress_widget.status_label.setText(self.loc.main.processing)
                    progress_widget.progress_bar.setRange(0, 0)
                case Translation.Status.DownloadFailed:
                    progress_widget.status_label.setText(self.loc.main.download_failed)
                    progress_widget.progress_bar.hide()
                case Translation.Status.DownloadSuccess:
                    item.setHidden(True)
                case Translation.Status.Ok:
                    item.setHidden(True)
                case status:
                    progress_widget.status_label.setText(str(status))
                    progress_widget.progress_bar.setRange(0, 0)

        for translation, item in self.items.copy().items():
            if translation.status in [
                Translation.Status.DownloadSuccess,
                Translation.Status.Ok,
            ]:
                item.setHidden(True)
                self.items.pop(translation)

        self.update()

    def download_thread(self):
        """
        Thread to download items from queue.
        """

        self.app.log.debug("Thread started.")

        while self.status == self.Status.Running:
            self.current_translation: Translation = self.queue.get()
            self.current_translation.status = Translation.Status.Processing
            tmp_path = self.app.get_tmp_dir()
            mod_id = self.current_translation.mod_id
            file_id = self.current_translation.file_id

            if self.current_translation._download:
                self.current_download = self.current_translation._download
            else:
                self.current_download = self.downloader.download_file(
                    mod_id, file_id, tmp_path
                )
            self.app.log.info(f"Downloading file {file_id} from mod {mod_id}...")

            downloaded_file = self.current_download.dl_path
            self.current_translation.status = Translation.Status.Downloading
            self.start_timer_signal.emit()
            if not downloaded_file.is_file():
                self.current_download.download()
            self.stop_timer_signal.emit()

            if downloaded_file.is_file():
                self.app.log.info(f"Processing file {downloaded_file.name!r}...")
                self.current_translation.status = Translation.Status.Processing
                self.update_progress()
                try:
                    strings = utils.import_from_archive(
                        downloaded_file, self.app.mainpage_widget.mods
                    )
                except Exception as ex:
                    self.log.error(
                        f"Failed to import translation from downloaded archive: {ex}",
                        exc_info=ex,
                    )
                    self.current_translation.status = Translation.Status.DownloadFailed

                else:
                    if (
                        self.current_translation.mod_id == 0
                        or self.current_translation.file_id == 0
                    ):
                        plugin_name: str = strings.keys()[0].lower()

                        for mod in self.app.mainpage_widget.mods:
                            if any(
                                plugin_name == plugin.name.lower()
                                for plugin in mod.plugins
                            ):
                                self.current_translation.original_mod_id = mod.mod_id
                                self.current_translation.original_file_id = mod.file_id
                                self.current_translation.original_version = mod.version

                    if strings:
                        self.current_translation.strings = strings
                        self.current_translation.save_translation()
                        self.current_translation.status = Translation.Status.Ok
                        self.app.database.add_translation(self.current_translation)
                        self.app.log.info("Processing complete.")
                    else:
                        self.app.log.warning(
                            "Translation does not contain any strings!"
                        )
                        self.current_translation.status = (
                            Translation.Status.DownloadFailed
                        )

                self.download_finished.emit()

            else:
                self.app.log.error("Download failed!")
                self.current_translation.status = Translation.Status.DownloadFailed

            self.update_progress()
            self.current_download = None
            self.current_translation = None
            self.queue.task_done()

            if self.queue.empty():
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

        parsed_query = urllib.parse.parse_qs(query)

        (key,) = parsed_query["key"]
        (expires,) = parsed_query["expires"]
        (user_id,) = parsed_query["user_id"]

        mod_details = self.app.api.get_mod_details("skyrimspecialedition", mod_id)
        mod_name: str = mod_details["name"]
        mod_version: str = mod_details["version"]
        timestamp = self.app.api.get_timestamp_of_file(
            "skyrimspecialedition", mod_id, file_id
        )

        installed_translation = self.app.database.get_translation_by_id(mod_id)

        if installed_translation:
            translation = installed_translation
            if installed_translation.version == mod_version:
                mb = qtw.QMessageBox(self.app.root)
                mb.setWindowTitle(self.mloc.already_installed)
                mb.setText(self.mloc.already_installed_text)
                utils.apply_dark_title_bar(mb)
                mb.setStandardButtons(mb.StandardButton.Ok)
                mb.exec()

                return
        else:
            translation = Translation(
                name=mod_name,
                mod_id=mod_id,
                file_id=file_id,
                version=mod_version,
                original_mod_id=0,
                original_file_id=0,
                original_version="0",
                path=self.app.database.userdb_path
                / self.app.user_config["language"]
                / mod_name,
                source=Translation.Source.NexusMods,
                timestamp=timestamp,
            )

        download = self.downloader.download_file(
            mod_id, file_id, self.app.get_tmp_dir(), key, int(expires)
        )
        translation._download = download

        item = qtw.QTreeWidgetItem(
            [
                translation.name,
                self.loc.main.waiting_for_download,
            ]
        )
        item.setFont(1, qtg.QFont("Consolas"))
        self.items[translation] = item
        self.downloads_widget.addTopLevelItem(item)

        self.queue.put(translation)

    def all_finished(self):
        """
        Shows messagebox to tell that all downloads in queue are finished.
        """

        self.app.database.save_database()

        self.downloads_widget.clear()
        self.items.clear()

        messagebox = qtw.QMessageBox(self.app.root)
        messagebox.setWindowTitle(self.loc.main.success)
        messagebox.setText(self.mloc.queue_finished)
        utils.apply_dark_title_bar(messagebox)
        messagebox.exec()

        self.queue_finished.disconnect(self.all_finished)
