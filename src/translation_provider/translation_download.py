"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from dataclasses import dataclass
import utilities as utils

from .file_download import FileDownload


@dataclass
class TranslationDownload:
    """
    Class for translation download entries for DownloadListDialog.
    """

    name: str
    mod_id: int

    original_mod: utils.Mod
    original_plugin: utils.Plugin

    source: utils.Source

    available_downloads: list[FileDownload]
