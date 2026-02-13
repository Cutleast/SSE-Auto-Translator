"""
Copyright (c) Cutleast
"""

from typing import Literal, Optional, override

from cutleast_core_lib.core.utilities.pydantic_utils import include_literal_defaults

from ..base_mod_id import BaseModId
from ..source import Source


@include_literal_defaults
class NxmModId(BaseModId, frozen=True):
    """
    Model for mod ids from Nexus Mods.
    """

    mod_id: int
    """The id of the mod."""

    file_id: Optional[int] = None
    """The id of the mod file, if any."""

    nm_game_id: str = "skyrimspecialedition"
    """The Nexus Mods game id of the mod. Defaults to "skyrimspecialedition"."""

    source: Literal[Source.NexusMods] = Source.NexusMods

    @override
    def __str__(self) -> str:
        string: str = str(self.mod_id)

        if self.file_id is not None:
            string += f" > {self.file_id}"

        return string
