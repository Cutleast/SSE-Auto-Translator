"""
Copyright (c) Cutleast
"""

import webbrowser

from cutleast_core_lib.core.multithreading.progress import ProgressUpdate
from cutleast_core_lib.core.utilities.exceptions import format_exception
from cutleast_core_lib.core.utilities.typing_utils import not_none
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QTreeWidgetItem

from core.downloader.file_download import FileDownload

from .item_widget import DownloadItemWidget


class DownloadItem(QTreeWidgetItem, QObject):  # type: ignore
    """
    Class for items in the Downloads tab.
    """

    remove_requested = Signal()
    """
    Signal emitted when the item should be removed from the queue.
    """

    __copy_text: str
    __download: FileDownload
    __widget: DownloadItemWidget

    def __init__(self, download: FileDownload) -> None:
        """
        Args:
            download (FileDownload): The download object that this item represents.
        """

        QObject.__init__(self)
        super().__init__()

        self.__copy_text = ""
        self.__download = download

        self.setText(0, self.__download.mod_details.display_name)
        self.setIcon(0, not_none(self.__download.source.get_icon()))

        self.__widget = DownloadItemWidget()

        self.__widget.copy_requested.connect(
            lambda: QApplication.clipboard().setText(self.__copy_text)
        )
        self.__widget.remove_requested.connect(self.remove_requested.emit)

    def init_widget(self, widget_column: int) -> None:
        """
        Initializes the widget for the download item.

        Args:
            widget_column (int): The column index where the widget will be displayed.
        """

        self.treeWidget().setItemWidget(self, widget_column, self.__widget)

    def set_interaction_required(self, download_url: str) -> None:
        """
        Sets the item to indicate that user interaction is required for the download.

        Args:
            download_url (str): The URL of the download that requires interaction.
        """

        self.__copy_text = download_url

        self.__widget.download_requested.disconnect()
        self.__widget.download_requested.connect(lambda: webbrowser.open(download_url))

        self.__widget.set_interaction_required()

    def set_running(self) -> None:
        """
        Sets the item to indicate that the download is currently running.
        """

        self.__widget.set_running()

    def set_failed(self, exception: Exception) -> None:
        """
        Sets the item to indicate that the download has failed.

        Args:
            exception (Exception): The exception that caused the failure.
        """

        self.__copy_text = format_exception(exception, False)
        self.__widget.set_failed(exception)

    def update_progress(self, progress_update: ProgressUpdate) -> None:
        """
        Updates the progress of the download item.

        Args:
            progress_update (ProgressUpdate): The progress update payload.
        """

        self.__widget.update_progress(progress_update)
