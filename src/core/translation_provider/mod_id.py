"""
Copyright (c) Cutleast
"""

from typing import Optional

from pydantic.dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class ModId:
    """
    Dataclass for identifying mods at their source.
    """

    mod_id: int
    """The provider specific id of the mod."""

    file_id: Optional[int] = None
    """The provider specific id of the mod file, if any."""

    nm_id: Optional[int] = None
    """The Nexus Mods id of the mod, if available."""

    nm_game_id: str = "skyrimspecialedition"
    """The Nexus Mods game id of the mod. Defaults to "skyrimspecialedition"."""
