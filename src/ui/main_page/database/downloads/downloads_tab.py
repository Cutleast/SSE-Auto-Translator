"""
Copyright (c) Cutleast
"""

from typing import override

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.core.utilities.blocking_thread import BlockingThread
from cutleast_core_lib.core.utilities.scale import scale_value
from PySide6.QtCore import Qt, QTimerEvent
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLCDNumber,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from core.downloader.download_manager import DownloadManager
from core.downloader.file_download import FileDownload
from core.translation_provider.nm_api.nxm_handler import NXMHandler
from core.translation_provider.provider import Provider

from .download_item import DownloadItem
from .downloads_toolbar import DownloadsToolbar


class DownloadsTab(QWidget):
    """
    Tab for Downloads.
    """

    __download_manager: DownloadManager
    __download_items: dict[FileDownload, DownloadItem]

    __vlayout: QVBoxLayout
    __toolbar: DownloadsToolbar
    __downloads_num_label: QLCDNumber
    __downloads_widget: QTreeWidget

    def __init__(self, download_manager: DownloadManager, provider: Provider) -> None:
        """
        Args:
            download_manager (DownloadManager): The download manager instance.
            provider (Provider): The translation provider instance.
        """

        super().__init__()

        self.__download_manager = download_manager
        self.__download_items = {}

        self.__init_ui()

        self.__toolbar.toggle_nxm_requested.connect(self.__toggle_nxm)
        self.__toolbar.toggle_pause_requested.connect(self.__toggle_pause)

        self.__download_manager.download_added.connect(self.__on_download_added)
        self.__download_manager.download_started.connect(self.__on_download_started)
        self.__download_manager.download_finished.connect(
            self.__remove_item_for_download
        )
        self.__download_manager.user_action_required.connect(
            self.__on_user_action_required
        )
        self.__download_manager.download_failed.connect(self.__on_download_failed)

        self.startTimer(1000, Qt.TimerType.PreciseTimer)

        # Highlight NXM button if the user has no Premium
        # FIXME: This crashes the app if there is no provider initialized
        if not provider.direct_downloads_possible():
            self.__toolbar.highlight_nxm_action()

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_downloads_widget()

    def __update(self) -> None:
        self.__downloads_num_label.display(len(self.__download_items))

    def __init_header(self) -> None:
        hlayout = QHBoxLayout()
        self.__vlayout.addLayout(hlayout)

        self.__toolbar = DownloadsToolbar()
        hlayout.addWidget(self.__toolbar)

        hlayout.addStretch()

        downloads_num_label = QLabel(self.tr("Downloads:"))
        downloads_num_label.setObjectName("h3")
        hlayout.addWidget(downloads_num_label)

        self.__downloads_num_label = QLCDNumber()
        self.__downloads_num_label.setDigitCount(4)
        hlayout.addWidget(self.__downloads_num_label)

    def __init_downloads_widget(self) -> None:
        self.__downloads_widget = QTreeWidget()
        self.__downloads_widget.setObjectName("download_list")
        self.__downloads_widget.setAlternatingRowColors(True)
        self.__downloads_widget.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)
        self.__downloads_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.__downloads_widget.setHeaderLabels(
            [self.tr("Name"), self.tr("Size"), self.tr("Progress")]
        )
        self.__downloads_widget.header().setStretchLastSection(False)
        self.__downloads_widget.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.__downloads_widget.setUniformRowHeights(True)
        self.__vlayout.addWidget(self.__downloads_widget)

    @override
    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)

        self.__downloads_widget.header().resizeSection(2, 300)

    def __on_download_added(self, download: FileDownload) -> None:
        download_item = DownloadItem(download)
        self.__downloads_widget.addTopLevelItem(download_item)

        download_item.init_widget(2)
        download_item.remove_requested.connect(
            lambda: self.__remove_item_for_download(download)
        )
        download_item.remove_requested.connect(
            lambda: self.__download_manager.remove_download_item(download)
        )

        def update_callback(payload: ProgressUpdate) -> None:
            if payload.maximum:
                download_item.setText(1, scale_value(payload.maximum))

            download_item.update_progress(payload)

        self.__download_items[download] = download_item
        self.__download_manager.add_download_item(download, update_callback)

        self.__update()

    def __on_download_started(self, download: FileDownload) -> None:
        if download not in self.__download_items:
            self.__on_download_added(download)

        download_item: DownloadItem = self.__download_items[download]
        download_item.set_running()

    def __on_user_action_required(
        self, download: FileDownload, download_url: str
    ) -> None:
        if download not in self.__download_items:
            self.__on_download_added(download)

        download_item: DownloadItem = self.__download_items[download]
        download_item.set_interaction_required(download_url)

    def __on_download_failed(self, download: FileDownload, exception: Exception) -> None:
        if download not in self.__download_items:
            self.__on_download_added(download)

        download_item: DownloadItem = self.__download_items[download]
        download_item.set_failed(exception)

    def __remove_item_for_download(self, download: FileDownload) -> None:
        if download not in self.__download_items:
            return  # we never had an item for the download

        download_item: DownloadItem = self.__download_items.pop(download)
        self.__downloads_widget.takeTopLevelItem(
            self.__downloads_widget.indexOfTopLevelItem(download_item)
        )
        self.__update()

    def __toggle_nxm(self, checked: bool) -> None:
        if checked:
            NXMHandler.get().bind()
        else:
            NXMHandler.get().unbind()

    def __check_nxm_link(self) -> None:
        if NXMHandler.has_instance():
            self.__toolbar.set_handle_nxm_action_checked(NXMHandler.get().is_bound())

    @override
    def timerEvent(self, event: QTimerEvent) -> None:
        super().timerEvent(event)

        self.__check_nxm_link()

    def __toggle_pause(self) -> None:
        self.setDisabled(True)

        if self.__download_manager.running:
            thread = BlockingThread(self.__download_manager.pause)
            thread.start()
        else:
            self.__download_manager.resume()

        self.__toolbar.update_toggle_pause_action(not self.__download_manager.running)

        self.setDisabled(False)
