"""
Copyright (c) Cutleast
"""

import logging
import os
from typing import Optional

import qtawesome as qta
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QPushButton, QTreeWidget, QTreeWidgetItem

from core.downloader.file_download import FileDownload
from core.translation_provider.nm_api.nm_api import NexusModsApi
from core.utilities.progress_update import ProgressUpdate
from core.utilities.scale import scale_value
from ui.widgets.progress_widget import ProgressWidget


class DownloadItem(QTreeWidgetItem, QObject):  # type: ignore[misc]
    """
    Class for items in the Downloads tab.

    TODO: Add button to remove a download from the queue
    """

    __update_signal = Signal(ProgressUpdate)

    finished_signal = Signal(object)
    """
    This signal gets emitted when the download is finished and can be removed.
    """

    remove_signal = Signal(object)
    """
    This signal gets emitted when the download should be removed from the queue.
    """

    log: logging.Logger = logging.getLogger("DownloadItem")

    download: FileDownload
    current_widget: Optional[ProgressWidget | QPushButton] = None

    def __init__(self, download: FileDownload) -> None:
        QObject.__init__(self)
        super().__init__()

        self.download = download
        self.__update_signal.connect(
            self.__update_progress, Qt.ConnectionType.QueuedConnection
        )

        self.setText(0, self.download.display_name)

    def __show_download_button(self) -> None:
        if isinstance(self.current_widget, QPushButton):
            return

        parent: QTreeWidget = self.treeWidget()

        button = QPushButton(
            qta.icon("ri.download-line", color=parent.palette().text().color()),
            self.tr("Free Download..."),
        )

        def open_download_page() -> None:
            url = NexusModsApi.create_nexus_mods_url(
                "skyrimspecialedition",
                self.download.mod_id,
                self.download.file_id,
                mod_manager=True,
            )

            self.log.debug(f"Opening {url!r}...")
            os.startfile(url)

            button.setIcon(
                qta.icon("fa5s.check", color=parent.palette().text().color())
            )

        button.clicked.connect(open_download_page)

        parent.setItemWidget(self, 2, button)
        self.current_widget = button

    def __show_progress_widget(self) -> None:
        if isinstance(self.current_widget, ProgressWidget):
            return

        parent: QTreeWidget = self.treeWidget()
        progress_widget = ProgressWidget(self)
        progress_widget.close_signal.connect(lambda: self.remove_signal.emit(self))
        parent.setItemWidget(self, 2, progress_widget)
        self.current_widget = progress_widget

    def update_progress(self, progress_update: ProgressUpdate) -> None:
        """
        Updates progress of the mod item. This method is thread-safe.

        Args:
            progress_update (ProgressUpdate): Progress update created by worker thread.
        """

        self.__update_signal.emit(progress_update)

    def __update_progress(self, progress_update: ProgressUpdate) -> None:
        match progress_update.status_text:
            case ProgressUpdate.Status.UserActionRequired:
                # User has no premium and must start download in browser
                self.__show_download_button()

            case ProgressUpdate.Status.Finished:
                self.finished_signal.emit(self)

            case ProgressUpdate.Status.Failed:
                self.__show_progress_widget()

                if (
                    isinstance(self.current_widget, ProgressWidget)
                    and progress_update.exception
                ):
                    self.current_widget.setException(progress_update.exception)

            case text:
                self.__show_progress_widget()

                if isinstance(self.current_widget, ProgressWidget):
                    self.current_widget.setProgress(
                        progress_update.current, progress_update.maximum
                    )

                if progress_update.speed is not None:
                    text = (text or "") + f" ({scale_value(progress_update.speed)}/s)"

                if text is not None and self.current_widget is not None:
                    self.current_widget.setText(text)

        if progress_update.maximum > 1 and progress_update.maximum != 100:
            self.setText(1, scale_value(progress_update.maximum))
