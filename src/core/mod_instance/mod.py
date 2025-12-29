"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from fnmatch import fnmatch
from functools import cache
from pathlib import Path
from typing import Optional, Self, override

from mod_manager_lib.core.instance.mod import Mod as BaseMod

from core.mod_file.mod_file import ModFile
from core.translation_provider.mod_id import ModId
from core.utilities.constants import DSD_FILE_PATTERN


class Mod(BaseMod):
    """
    Class for mods, their mod files and their metadata.
    """

    modfiles: list[ModFile]
    """List of translatable files in mod."""

    @classmethod
    def from_mml_mod(cls, mml_mod: BaseMod, modfiles: list[ModFile]) -> Self:
        """Constructs a mod from the base model."""

        return cls(
            **mml_mod.model_dump(exclude={"mod_conflicts", "file_conflicts"}),
            modfiles=modfiles,
        )

    @property
    def name(self) -> str:
        """The mod's display name."""

        return self.display_name

    @property
    @cache
    def mod_id(self) -> Optional[ModId]:
        """The mod id of the mod identifying it at its source."""

        if self.metadata.mod_id:
            return ModId(
                mod_id=self.metadata.mod_id,
                file_id=self.metadata.file_id,
                nm_game_id=self.metadata.game_id,
                installation_file_name=self.metadata.file_name,
            )

    @property
    def version(self) -> str:
        """The mod's version."""

        return self.metadata.version

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
        return hash((self.display_name, self.path, self.metadata))
