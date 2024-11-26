"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from core.utilities.mod import Mod


class ModManager:
    """
    Base class for every mod manager instance.
    """

    name: str = None

    def get_instances(self) -> list[str]:
        """
        Loads and returns a list of all mod instances
        that are managed by this mod manager.
        """

        raise NotImplementedError

    def get_modlist(self, instance_name: str, instance_profile: str | None = None) -> list[Mod]:
        """
        Loads and returns a list of all enabled mods
        with paying attention for conflict rules (Vortex).

        MO2: Loads `instance_profile` if given else "Default".
        """

        raise NotImplementedError
    
    def get_instance_profiles(self, instance_name: str) -> list[str]:
        """
        Gets a list of profiles in `instance_name`.

        Mainly for ModOrganizer Instances.
        """

        raise NotImplementedError
