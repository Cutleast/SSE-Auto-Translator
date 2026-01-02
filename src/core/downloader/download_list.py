"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import override

from pydantic import BaseModel, TypeAdapter

from .file_download import FileDownload
from .mod_info import ModInfo

DownloadList = TypeAdapter(list["DownloadListItem"])
"""
Type adapter for an exportable and importable list of pre-selected translation downloads.
"""


class DownloadListItem(BaseModel):
    """
    Model for a single item of an exportable and importable list of pre-selected
    translation downloads.
    """

    mod: ModInfo
    """The mod, the download is for."""

    mod_file: Path
    """The mod file path (relative to the game's "Data" folder)."""

    translation: ModInfo
    """The translation to download."""

    download: FileDownload
    """The file to download."""

    @override
    def __str__(self) -> str:
        return f"{self.mod.display_name} > {self.mod_file} > {self.translation.display_name}"
