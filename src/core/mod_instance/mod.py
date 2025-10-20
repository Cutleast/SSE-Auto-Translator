"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from enum import Enum, auto
from fnmatch import fnmatch
from functools import cache
from pathlib import Path
from typing import Optional, override

from pydantic import BaseModel

from core.mod_file.mod_file import ModFile
from core.translation_provider.mod_id import ModId
from core.utilities.constants import DSD_FILE_PATTERN


class Mod(BaseModel):
    """
    Class for mods, their mod files and their metadata.
    """

    name: str
    """Display name of the mod."""

    path: Path
    """Path to the mod's folder."""

    modfiles: list[ModFile]
    """List of translatable files in mod."""

    mod_id: Optional[ModId]
    """Identifier of this mod at its source."""

    version: str
    """Local version of the mod."""

    class Type(Enum):
        """
        Type of the mod.
        """

        Regular = auto()
        """
        The mod is a regular mod.
        """

        Separator = auto()
        """
        The mod is a separator.
        """

    mod_type: Type = Type.Regular
    """
    Type of the mod.
    """

    @property
    @cache
    def dsd_files(self) -> list[Path]:
        """
        List of all DSD files in the mod, excluding the ones from generated Output mod.
        """

        return [
            file.relative_to(self.path)
            for file in self.path.glob(DSD_FILE_PATTERN)
            if (  # Do not import DSD files from generated Output mod
                not fnmatch(file.name, "*_SSEAT.json")
                and file.stem.lower() != "sse-at_output"
            )
        ]

    @override
    def __hash__(self) -> int:
        return hash((self.name, self.path, self.mod_id))
