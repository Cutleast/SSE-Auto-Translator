"""
Copyright (c) Cutleast
"""

import logging

from core.mod_instance.mod import Mod
from core.mod_instance.plugin import Plugin

from ..app_test import AppTest


class CoreTest(AppTest):
    """
    Base class for all core-related tests.
    """

    log: logging.Logger = logging.getLogger("CoreTest")

    def get_mod_by_name(self, mod_name: str) -> Mod:
        """
        Gets a mod by its name from the loaded mod instance.

        Args:
            mod_name (str): The name of the mod

        Raises:
            ValueError: When no mod with the specified name is found

        Returns:
            Mod: The mod
        """

        try:
            mod: Mod = next(
                (mod for mod in self.modinstance().mods if mod.name == mod_name)
            )
        except StopIteration:
            raise ValueError(f"No mod with name {mod_name} found in mod instance.")

        return mod

    def get_plugin_from_mod(self, mod: Mod, plugin_name: str) -> Plugin:
        """
        Gets a plugin by its name from the specified mod.

        Args:
            mod (Mod): Mod to get plugin from
            plugin_name (str): The name of the plugin

        Returns:
            Plugin: The plugin
        """

        try:
            plugin: Plugin = next(
                (plugin for plugin in mod.plugins if plugin.name == plugin_name)
            )
        except StopIteration:
            raise ValueError(f"No plugin with name {plugin_name} found in mod.")

        return plugin

    def get_plugin_from_mod_name(self, mod_name: str, plugin_name: str) -> Plugin:
        """
        Gets a plugin by its name from the specified mod.

        Args:
            mod_name (str): Name of the mod to get plugin from
            plugin_name (str): The name of the plugin

        Raises:
            ValueError: When no mod with the specified name is found
            ValueError: When no plugin with the specified name is found

        Returns:
            Plugin: The plugin
        """

        mod: Mod = self.get_mod_by_name(mod_name)

        return self.get_plugin_from_mod(mod, plugin_name)
