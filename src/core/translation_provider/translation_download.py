"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from dataclasses import dataclass

from core.utilities.mod import Mod
from core.utilities.plugin import Plugin
from core.utilities.source import Source

from .file_download import FileDownload


@dataclass
class TranslationDownload:
    """
    Class for translation download entries for DownloadListDialog.
    """

    name: str
    mod_id: int

    original_mod: Mod
    original_plugin: Plugin

    source: Source

    available_downloads: list[FileDownload]
