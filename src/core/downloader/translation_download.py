"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from dataclasses import dataclass
from typing import override

from core.translation_provider.mod_id import ModId
from core.translation_provider.source import Source

from .file_download import FileDownload


@dataclass
class TranslationDownload:
    """
    Class for download entries in DownloadListDialog.
    """

    name: str
    """
    The name of the translation.
    """

    mod_id: ModId
    """
    Mod identifier used to open the mod page.
    """

    modfile_name: str
    """
    The name of the mod file this translation is for.
    """

    source: Source
    """
    The source of the translation.
    """

    available_downloads: list[FileDownload]
    """
    List of available downloads.
    """

    @override
    def __hash__(self) -> int:
        return hash((self.mod_id, self.modfile_name, self.source.name))
