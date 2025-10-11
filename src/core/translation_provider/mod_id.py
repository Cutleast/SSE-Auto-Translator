"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from pydantic import BaseModel, ConfigDict

from core.translation_provider.source import Source


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

    installation_file_name: Optional[str] = None
    """The full name of the original download archive, if available."""

    @override
    def __hash__(self) -> int:
        return hash((self.mod_id, self.file_id, self.nm_id, self.nm_game_id))

    def estimate_source(self, is_french: bool = False) -> Source:
        """
        Attempts to guess the source of the mod based on the existence of mod id and
        file id.

        Args:
            is_french (bool, optional):
                Whether the mod is in French. This determines, whether the CDT is
                returned if there is no file id. Defaults to False.

        Returns:
            Source:
                The estimated source of the mod or `Source.Local` if the source could
                not be estimated.
        """

        if self.mod_id and self.file_id and self.nm_id is None:
            return Source.NexusMods

        if (
            self.mod_id
            and self.file_id is None
            and self.nm_id is not None
            and is_french
        ):
            return Source.Confrerie

        return Source.Local
