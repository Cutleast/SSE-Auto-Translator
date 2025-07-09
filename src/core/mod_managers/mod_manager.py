"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from pathlib import Path

from core.mod_instance.mod_instance import ModInstance


class ModManager:
    """
    Base class for every mod manager instance.
    """

    class Type(Enum):
        """Enum for the available mod manager types."""

        ModOrganizer = "Mod Organizer 2"
        Vortex = "Vortex"

        def get_mod_manager_class(self) -> type[ModManager]:
            """
            Returns:
                type[ModManager]: Class for this mod manager type.
            """

            from .modorganizer import ModOrganizer
            from .vortex import Vortex

            mod_managers: dict[ModManager.Type, type[ModManager]] = {
                ModManager.Type.ModOrganizer: ModOrganizer,
                ModManager.Type.Vortex: Vortex,
            }

            return mod_managers[self]

    @abstractmethod
    def get_instances(self) -> list[str]:
        """
        Loads and returns a list of all mod instances
        that are managed by this mod manager.
        """

    @abstractmethod
    def load_mod_instance(
        self,
        instance_name: str,
        instance_profile: str | None = None,
        instance_path: Path | None = None,
    ) -> ModInstance:
        """
        Loads and returns a modinstance with paying attention for
        conflict rules (Vortex).

        MO2: Loads the specified profile if given else "Default".
        """

    @abstractmethod
    def get_instance_profiles(
        self, instance_name: str, instance_path: Path | None = None
    ) -> list[str]:
        """
        Gets a list of profiles in `instance_name`.

        Mainly for ModOrganizer Instances.
        """
