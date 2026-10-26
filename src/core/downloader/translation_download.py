"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
GNU General Public License v3.0.
"""

from pydantic import BaseModel

from .file_download import FileDownload
from .mod_info import ModInfo


class TranslationDownload(BaseModel, frozen=True):
    """
    Class for download entries in DownloadListDialog.
    """

    mod_info: ModInfo
    """Mod details like name and source."""

    available_downloads: list[FileDownload]
    """List of available downloads."""
