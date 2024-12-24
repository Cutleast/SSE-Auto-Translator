"""
Copyright (c) Cutleast
"""

import qtawesome as qta
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLCDNumber,
    QMessageBox,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from app_context import AppContext
from core.downloader.download_manager import DownloadManager
from core.downloader.file_download import FileDownload
from core.utilities.blocking_thread import BlockingThread

from .download_item import DownloadItem
from .downloads_toolbar import DownloadsToolbar


class DownloadsTab(QWidget):
    """
    Tab for Downloads.
    """

    download_manager: DownloadManager

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

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__init_header()
        self.__init_downloads_widget()

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
        self.__downloads_widget.setAlternatingRowColors(True)
        self.__downloads_widget.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)
        self.__downloads_widget.setHeaderLabels(
            [self.tr("Name"), self.tr("Size"), self.tr("Progress")]
        )
        self.__downloads_widget.header().setStretchLastSection(False)
        self.__downloads_widget.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.__vlayout.addWidget(self.__downloads_widget)

    def __add_download(self, download: FileDownload) -> None:
        download_item = DownloadItem(download)
        download_item.finished_signal.connect(self.__download_finished)
        self.__downloads_widget.addTopLevelItem(download_item)
        self.__download_items.append(download_item)

        self.download_manager.add_download_item(download, download_item.update_progress)

    def __download_finished(self, download_item: DownloadItem) -> None:
        download_item.setHidden(True)
        self.__downloads_widget.takeTopLevelItem(
            self.__downloads_widget.indexOfTopLevelItem(download_item)
        )
        self.__download_items.remove(download_item)

    def stop(self) -> None:
        # TODO: Reevaluate this
        message_box = QMessageBox(QApplication.activeModalWidget())
        message_box.setWindowTitle(self.tr("Stop installation?"))
        message_box.setText(
            self.tr(
                "Are you sure you want to stop the installation? "
                "Once stopped, the process cannot be resumed!"
            )
        )
        message_box.setStandardButtons(
            QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes
        )
        message_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        if message_box.exec() != QMessageBox.StandardButton.Yes:
            return

        self.__toolbar.setDisabled(True)

        thread = BlockingThread(self.download_manager.stop)
        thread.start()

    def toggle_pause(self) -> None:
        self.setDisabled(True)

        if self.download_manager.running:
            thread = BlockingThread(self.download_manager.pause)
            thread.start()
            self.__toolbar.toggle_pause_action.setText(self.tr("Resume"))
            self.__toolbar.toggle_pause_action.setIcon(
                qta.icon("fa5s.play", color=self.palette().text().color())
            )
        else:
            self.download_manager.resume()
            self.__toolbar.toggle_pause_action.setText(self.tr("Pause"))
            self.__toolbar.toggle_pause_action.setIcon(
                qta.icon("fa5s.pause", color=self.palette().text().color())
            )

        self.setDisabled(False)
        self.__toolbar.stop_action.setDisabled(not self.download_manager.running)
