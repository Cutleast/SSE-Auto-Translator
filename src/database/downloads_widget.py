"""
This file is part of SEE Auto Translator
and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import urllib.parse
from enum import Enum, auto
from pathlib import Path
from queue import Queue

import qtpy.QtCore as qtc
import qtpy.QtWidgets as qtw

import utilities as utils
from main import MainApp
from nm_api import Download, Downloader

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

    class Status(Enum):
        Running = auto()
        Paused = auto()
        Stopped = auto()

    current_translation: Translation = None
    current_download: Download = None

    status: Status = Status.Running

    def __init__(self, app: MainApp):
        super().__init__()

        self.app = app
        self.loc = app.loc
        self.mloc = app.loc.database

        self.queue = Queue()
        self.downloader = Downloader(self.app.api, "skyrimspecialedition")
        self.thread = utils.Thread(self.download_thread)
        self.thread.start()

        self.startTimer(100, qtc.Qt.TimerType.PreciseTimer)

        vlayout = qtw.QVBoxLayout()
        self.setLayout(vlayout)

        self.downloads_widget = qtw.QTreeWidget()
        self.downloads_widget.setAlternatingRowColors(True)
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

    def timerEvent(self, event: qtc.QTimerEvent):
        super().timerEvent(event)

        self.update_progress()

    def update_progress(self):
        """
        Updates progress of current downloading translation.
        """

        if self.current_download and self.current_translation:
            match self.current_translation.status:
                case Translation.Status.Downloading:
                    if (
                        self.current_download.current_size
                        and self.current_download.previous_size
                    ):
                        cur_size = utils.scale_value(self.current_download.current_size)
                        tot_size = utils.scale_value(self.current_download.file_size)
                        spd = (
                            self.current_download.current_size
                            - self.current_download.previous_size
                        ) * 10
                        cur_speed = utils.scale_value(spd) + "/s"
                        percentage = f"{(self.current_download.current_size / self.current_download.file_size * 100):.2f} %"
                        status = f"{self.loc.main.downloading} ({cur_size}/{tot_size} - {percentage} - {cur_speed})"
                    else:
                        status = self.loc.main.downloading

                    self.current_download.previous_size = (
                        self.current_download.current_size
                    )

                    self.current_translation.tree_item.setText(1, status)
                case Translation.Status.Processing:
                    self.current_translation.tree_item.setText(
                        1, self.loc.main.processing
                    )
                case Translation.Status.DownloadFailed:
                    self.current_translation.tree_item.setText(
                        1, self.loc.main.download_failed
                    )
                case Translation.Status.DownloadSuccess:
                    self.current_translation.tree_item.setText(
                        1, self.loc.main.download_success
                    )
                case status:
                    self.current_translation.tree_item.setText(1, str(status))

        self.update()

    def download_thread(self):
        """
        Thread to download items from queue.
        """

        self.app.log.debug("Thread started.")

        while self.status == self.Status.Running:
            self.current_translation: Translation = self.queue.get()
            self.current_translation.status = Translation.Status.Downloading
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
            if not downloaded_file.is_file():
                self.current_download.download()

            if downloaded_file.is_file():
                self.app.log.info(f"Processing file {downloaded_file.name!r}...")
                self.current_translation.status = Translation.Status.Processing
                strings = utils.import_from_archive(
                    downloaded_file, self.app.mainpage_widget.mods
                )

                if (
                    self.current_translation.mod_id == 0
                    or self.current_translation.file_id == 0
                ):
                    plugin_name: str = strings.keys()[0].lower()

                    for mod in self.app.mainpage_widget.mods:
                        if any(
                            plugin_name == plugin.name.lower() for plugin in mod.plugins
                        ):
                            self.current_translation.original_mod_id = mod.mod_id
                            self.current_translation.original_file_id = mod.file_id
                            self.current_translation.original_version = mod.version

                if strings:
                    self.current_translation.strings = strings
                    self.current_translation.save_translation()
                    self.current_translation.status = Translation.Status.Ok
                    self.current_translation.tree_item.setHidden(True)
                    self.app.database.add_translation(self.current_translation)
                    self.app.log.info("Processing complete.")
                else:
                    self.app.log.warning("Translation does not contain any strings!")
                    self.current_translation.status = Translation.Status.DownloadFailed

                self.download_finished.emit()

            else:
                self.app.log.error("Download failed!")
                self.current_translation.status = Translation.Status.DownloadFailed

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
            )

        download = self.downloader.download_file(
            mod_id, file_id, self.app.get_tmp_dir(), key, int(expires)
        )
        translation._download = download

        item = qtw.QTreeWidgetItem(
            [
                translation.name,
                self.app.loc.main.waiting_for_download,
            ]
        )
        translation.tree_item = item
        self.downloads_widget.addTopLevelItem(item)

        self.queue.put(translation)

    def all_finished(self):
        """
        Shows messagebox to tell that all downloads in queue are finished.
        """

        messagebox = qtw.QMessageBox(self.app.root)
        messagebox.setWindowTitle(self.loc.main.success)
        messagebox.setText(self.mloc.queue_finished)
        utils.apply_dark_title_bar(messagebox)
        messagebox.exec()

        self.queue_finished.disconnect(self.all_finished)
