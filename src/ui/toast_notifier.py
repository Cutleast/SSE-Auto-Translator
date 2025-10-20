"""
Copyright (c) Cutleast
"""

from typing import Optional

from cutleast_core_lib.ui.widgets.toast import Toast
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication

from core.downloader.download_manager import DownloadManager


class ToastNotifier(QObject):
    """
    Class for showing various notifications via Toasts.
    """

    __download_manager: Optional[DownloadManager] = None
    __downloads_finished_toast: Optional[Toast] = None

    def set_download_manager(self, download_manager: DownloadManager) -> None:
        """
        Sets and connects a download manager.

        Args:
            download_manager (DownloadManager): Download manager.
        """

        self.__download_manager = download_manager
        self.__downloads_finished_toast = Toast(
            self.tr("All downloads finished!"), duration=5
        )
        self.__downloads_finished_toast.setIcon(QApplication.windowIcon())
        self.__download_manager.finished.connect(self.__downloads_finished_toast.show)
        self.__download_manager.finished.connect(lambda: print("SHOWING TOAST..."))
