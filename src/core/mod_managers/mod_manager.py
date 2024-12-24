"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from abc import abstractmethod
from pathlib import Path

from core.mod_instance.mod_instance import ModInstance


class ModManager:
    """
    Base class for every mod manager instance.
    """

    name: str

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
