"""
Copyright (c) Cutleast
"""

from typing import override

import qtawesome as qta
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QShowEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLCDNumber,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from app_context import AppContext
from core.downloader.download_manager import DownloadManager
from core.downloader.file_download import FileDownload
from core.translation_provider.nm_api.nxm_handler import NXMHandler
from core.translation_provider.provider import Provider
from core.utilities.blocking_thread import BlockingThread

from .download_item import DownloadItem
from .downloads_toolbar import DownloadsToolbar


class DownloadsTab(QWidget):
    """
    Tab for Downloads.
    """

    download_manager: DownloadManager
    provider: Provider
    nxm_listener: NXMHandler

    __download_items: list[DownloadItem]

    __vlayout: QVBoxLayout
    __toolbar: DownloadsToolbar
    __downloads_num_label: QLCDNumber
    __downloads_widget: QTreeWidget

    def __init__(self) -> None:
        super().__init__()

        self.__download_items = []

        self.__init_ui()

        AppContext.get_app().ready_signal.connect(self.__post_init)

    def __post_init(self) -> None:
        self.download_manager = AppContext.get_app().download_manager
        self.download_manager.download_added.connect(self.__add_download)

        self.provider = AppContext.get_app().provider
        self.nxm_listener = AppContext.get_app().nxm_listener
        AppContext.get_app().timer_signal.connect(self.__check_nxm_link)

        # Highlight NXM button if the user has no Premium
        if not self.provider.direct_downloads_possible():
            self.__toolbar.widgetForAction(
                self.__toolbar.handle_nxm_action
            ).setObjectName("accent_button")
            self.__toolbar.setStyleSheet(self.styleSheet())

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

        self.__toolbar = DownloadsToolbar(self)
        hlayout.addWidget(self.__toolbar)

        hlayout.addStretch()

        downloads_num_label = QLabel(self.tr("Downloads:"))
        downloads_num_label.setObjectName("relevant_label")
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
        self.__vlayout.addWidget(self.__downloads_widget)

    @override
    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)

        self.__downloads_widget.header().resizeSection(2, 300)

    def __add_download(self, download: FileDownload) -> None:
        download_item = DownloadItem(download)
        download_item.finished_signal.connect(self.__remove_download_item)
        download_item.remove_signal.connect(self.__remove_download_item)
        download_item.remove_signal.connect(
            lambda: self.download_manager.remove_download_item(download)
        )
        self.__downloads_widget.addTopLevelItem(download_item)
        self.__download_items.append(download_item)
        self.download_manager.add_download_item(download, download_item.update_progress)

        self.__update()

    def __remove_download_item(self, download_item: DownloadItem) -> None:
        download_item.setHidden(True)
        self.__downloads_widget.takeTopLevelItem(
            self.__downloads_widget.indexOfTopLevelItem(download_item)
        )
        self.__download_items.remove(download_item)
        self.__update()

    def toggle_nxm(self) -> None:
        if self.__toolbar.handle_nxm_action.isChecked():
            self.nxm_listener.bind()
        else:
            self.nxm_listener.unbind()

    def __check_nxm_link(self) -> None:
        self.__toolbar.handle_nxm_action.setChecked(self.nxm_listener.is_bound())

    def toggle_pause(self) -> None:
        text_color: QColor = self.palette().text().color()
        self.setDisabled(True)

        if self.download_manager.running:
            thread = BlockingThread(self.download_manager.pause)
            thread.start()
            self.__toolbar.toggle_pause_action.setText(self.tr("Resume"))
            self.__toolbar.toggle_pause_action.setIcon(
                qta.icon("fa5s.play", color=text_color)
            )
        else:
            self.download_manager.resume()
            self.__toolbar.toggle_pause_action.setText(self.tr("Pause"))
            self.__toolbar.toggle_pause_action.setIcon(
                qta.icon("fa5s.pause", color=text_color)
            )

        self.setDisabled(False)
