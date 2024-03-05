"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from utilities import Mod


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

    def get_modlist(self, instance_name: str) -> list[Mod]:
        """
        Loads and returns a list of all enabled mods
        with paying attention for conflict rules (Vortex).
        """

        raise NotImplementedError
