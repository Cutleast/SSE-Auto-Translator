"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from pydantic import BaseModel, ConfigDict


class ModId(BaseModel):
    """
    Dataclass for identifying mods at their source.
    """

    model_config = ConfigDict(frozen=True)

    mod_id: int
    """The provider specific id of the mod."""

    file_id: Optional[int] = None
    """The provider specific id of the mod file, if any."""

    nm_id: Optional[int] = None
    """The Nexus Mods id of the mod, if available."""

    nm_game_id: str = "skyrimspecialedition"
    """The Nexus Mods game id of the mod. Defaults to "skyrimspecialedition"."""

    @override
    def __hash__(self) -> int:
        return hash((self.mod_id, self.file_id, self.nm_id, self.nm_game_id))
