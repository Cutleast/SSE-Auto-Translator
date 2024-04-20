"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from enum import StrEnum
from dataclasses import dataclass

import qtpy.QtCore as qtc
import qtpy.QtWidgets as qtw

import utilities as utils


@dataclass
class FileDownload(qtc.QObject):
    """
    Class for single file downloads.
    """

    name: str
    source: utils.Source
    mod_id: int
    file_id: int = None

    original_mod: utils.Mod = None

    file_name: str = None
    direct_url: str = None

    tree_item: qtw.QTreeWidgetItem = None
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

    def __hash__(self):
        return hash((self.mod_id, self.file_id, self.source))
