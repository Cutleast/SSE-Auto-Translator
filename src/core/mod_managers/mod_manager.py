"""
Copyright (c) Cutleast
"""

from enum import StrEnum

from cutleast_core_lib.core.cache.function_cache import FunctionCache

from .mod_manager_api import ModManagerApi


class ModManager(StrEnum):
    """Enum for the available mod manager types."""

    ModOrganizer = "Mod Organizer 2"
    Vortex = "Vortex"

    @FunctionCache.cache
    def get_api(self) -> ModManagerApi:
        """
        Returns:
            ModManagerApi: Returns the API for this mod manager.
        """

        match self:
            case ModManager.ModOrganizer:
                from .modorganizer.modorganizer_api import ModOrganizerApi

                return ModOrganizerApi()
            case ModManager.Vortex:
                from .vortex.vortex_api import VortexApi

                return VortexApi()
