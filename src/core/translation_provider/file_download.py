"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from dataclasses import dataclass
from enum import StrEnum

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QTreeWidgetItem

from core.utilities.mod import Mod
from core.utilities.source import Source


@dataclass
class FileDownload(QObject):
    """
    Class for single file downloads.
    """

    name: str
    source: Source
    mod_id: int
    file_id: int = None

    original_mod: Mod = None

    file_name: str = None
    direct_url: str = None

    tree_item: QTreeWidgetItem = None
    """
    Item in "Downloads" Tab.
    """

    class Status(StrEnum):
        """
        Enum for different Statuses
        """

        WaitingForDownload = "Waiting for Download"
        Downloading = "Downloading"
        DownloadSuccess = "Download successful"
        DownloadFailed = "Download failed"
        Processing = "Processing"

    status: Status = Status.WaitingForDownload
