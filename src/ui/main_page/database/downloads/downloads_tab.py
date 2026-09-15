"""
Copyright (c) Cutleast
"""

import webbrowser
from typing import Optional, cast, override

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.core.utilities.blocking_thread import BlockingThread
from cutleast_core_lib.core.utilities.reverse_dict import reverse_dict
from cutleast_core_lib.core.utilities.scale import scale_value
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QShowEvent
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from core.downloader.download_manager import DownloadManager
from core.downloader.file_download import FileDownload
from core.translation_provider.nm_api.nxm_handler import NXMHandler
from core.translation_provider.provider import TranslationProvider
from core.translation_provider.source import Source

from .download_item import DownloadItem
from .downloads_menu import DownloadsMenu
from .downloads_toolbar import DownloadsToolbar


class DownloadsTab(QWidget):
    """
    Tab for Downloads.
    """

    __nxm_update_timer: QTimer

    __download_manager: DownloadManager
    __download_items: dict[FileDownload, DownloadItem]

    __vlayout: QVBoxLayout
    __toolbar: DownloadsToolbar
    __downloads_num_label: QLabel
    __downloads_widget: QTreeWidget
    __downloads_menu: DownloadsMenu

    def __init__(
        self, download_manager: DownloadManager, provider: TranslationProvider
    ) -> None:
        """
        Args:
            download_manager (DownloadManager): The download manager instance.
            provider (TranslationProvider): The translation provider instance.
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
        self.__download_manager.progress_updated.connect(self.__on_progress_updated)

        self.__downloads_widget.customContextMenuRequested.connect(
            self.__on_context_menu_requested
        )
        self.__downloads_menu.open_modpage_requested.connect(self.__open_modpage)

        self.__nxm_update_timer = QTimer(
            self, interval=1000, timerType=Qt.TimerType.PreciseTimer
        )
        self.__nxm_update_timer.timeout.connect(self.__check_nxm_link)
        self.__nxm_update_timer.start()

        self.__toolbar.set_handle_nxm_action_enabled(
            provider.is_source_available(Source.NexusMods)
        )

        # Highlight NXM button if the user has no Premium
        if provider.is_available and not provider.direct_downloads_possible():
            self.__toolbar.highlight_nxm_action()

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.__vlayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_downloads_widget()
        self.__init_context_menu()

    def __update(self) -> None:
        self.__downloads_num_label.setText(str(len(self.__download_items)))

    def __init_header(self) -> None:
        self.__toolbar = DownloadsToolbar()
        self.__vlayout.addWidget(self.__toolbar)

        first_action: QAction = self.__toolbar.actions()[0]

        title_label = QLabel(self.tr("Downloads"))
        title_label.setProperty("title", True)
        self.__toolbar.insertWidget(first_action, title_label)

        self.__toolbar.insertSeparator(first_action)

        self.__toolbar.addSeparator()

        downloads_num_label = QLabel(self.tr("Running Downloads:"))
        downloads_num_label.setProperty("subtitle", True)
        downloads_num_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            downloads_num_label.sizePolicy().verticalPolicy(),
        )
        downloads_num_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.__toolbar.addWidget(downloads_num_label)

        self.__downloads_num_label = QLabel("0")
        self.__downloads_num_label.setProperty("subtitle", True)
        self.__toolbar.addWidget(self.__downloads_num_label)

    def __init_downloads_widget(self) -> None:
        self.__downloads_widget = QTreeWidget()
        self.__downloads_widget.setObjectName("download_list")
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

    def __init_context_menu(self) -> None:
        self.__downloads_menu = DownloadsMenu()
        self.__downloads_widget.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )

    def __get_selected_download(self) -> Optional[FileDownload]:
        current_item = cast(
            Optional[DownloadItem], self.__downloads_widget.currentItem()
        )
        if current_item is None:
            return

        items: dict[DownloadItem, FileDownload] = reverse_dict(self.__download_items)
        return items[current_item]

    def __on_context_menu_requested(self) -> None:
        selected_download: Optional[FileDownload] = self.__get_selected_download()
        if selected_download is None:
            return

        self.__downloads_menu.open(selected_download.source)

    def __open_modpage(self) -> None:
        selected_download: Optional[FileDownload] = self.__get_selected_download()
        if selected_download is None:
            return

        webbrowser.open(selected_download.mod_details.modpage_url)

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

        self.__download_items[download] = download_item
        self.__download_manager.add_download_item(download)

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

    def __on_progress_updated(
        self, download: FileDownload, payload: ProgressUpdate
    ) -> None:
        """
        Updates the UI for the progress of a queued download.

        Args:
            download (FileDownload): The download whose progress changed.
            payload (ProgressUpdate): The new progress data.
        """

        download_item: Optional[DownloadItem] = self.__download_items.get(download)
        if download_item is None:
            return

        if payload.maximum:
            download_item.setText(1, scale_value(payload.maximum))

        download_item.update_progress(payload)

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

    def __toggle_pause(self) -> None:
        self.setDisabled(True)

        if self.__download_manager.running:
            thread = BlockingThread(self.__download_manager.pause)
            thread.start()
        else:
            self.__download_manager.resume()

        self.__toolbar.set_paused(not self.__download_manager.running)

        self.setDisabled(False)
