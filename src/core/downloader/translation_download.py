"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from dataclasses import dataclass
from typing import Optional

from core.mod_instance.mod import Mod
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

    mod_id: int
    """
    Nexus Mods mod id used to open the mod page.
    """

    plugin_name: str
    """
    The name of the plugin this translation is for.
    """

    source: Source
    """
    The source of the translation.
    """

    available_downloads: list[FileDownload]
    """
    List of available downloads.
    """

    original_mod: Optional[Mod] = None
    """
    Installed mod the translation is for.
    """

    def __hash__(self) -> int:
        return hash((self.mod_id, self.plugin_name, self.source.name))