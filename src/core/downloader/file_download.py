"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from dataclasses import dataclass, field
from typing import Optional, override

from core.mod_instance.mod import Mod
from core.translation_provider.mod_id import ModId
from core.translation_provider.source import Source


@dataclass
class FileDownload:
    """
    Class for single file downloads.
    """

    display_name: str
    """
    Display name of the download.
    """

    source: Source
    """
    Source the download is from.
    """

    mod_id: ModId
    """
    Nexus Mods mod id.
    """

    file_name: Optional[str] = None
    """
    Full name of the downloaded file.
    """

    original_mod: Optional[Mod] = None
    """
    Installed mod the translation is for.
    """

    stale: bool = field(default=False)
    """
    Whether the download is stale and should be removed as soon as a thread picks it up.
    """

    @override
    def __hash__(self) -> int:
        return hash((self.source.name, self.mod_id, self.file_name))
