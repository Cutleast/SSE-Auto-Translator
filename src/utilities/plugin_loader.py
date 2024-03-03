"""
This file is part of SEE Auto Translator
and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from pathlib import Path

from .constants import BASE_GAME_PLUGINS, AE_CC_PLUGINS
from .plugin import Plugin


class PluginLoader:
    """
    Class to load plugins in right order.
    """

    loadorder_txt: Path = None
    mods_folder: Path = None
    loadorder: list[Plugin] = None

    def __init__(self, loadorder_txt: Path, mods_folder: Path):
        self.loadorder_txt = loadorder_txt
        self.mods_folder = mods_folder

    def process_loadorder(self):
        """
        Reads loadorder.txt and creates a
        list of paths to the plugin files
        in their respective order.
        """

        loadorder: list[str] = []
        with open(self.loadorder_txt, "r", encoding="utf8") as file:
            for line in file.readlines():
                if not line.startswith("#") and line.strip():
                    loadorder.append(line.strip())

        self.loadorder: list[Plugin] = []
        for plugin_name in loadorder:
            plugin_paths = list(self.mods_folder.glob(f"*/{plugin_name}"))
            if plugin_paths:
                plugin = Plugin(
                    plugin_paths[0].name, plugin_paths[0], Plugin.Status.Unknown
                )
                self.loadorder.append(plugin)
            else:
                plugin = Plugin(
                    plugin_name,
                    self.mods_folder / plugin_name,
                    Plugin.Status.FileNotFound,
                )
                self.loadorder.append(plugin)

        return self.loadorder

    def clean_base_game_plugins(self):
        """
        Removes base game plugins from self.loadorder
        and returns the remaining loadorder.
        """

        loadorder = [
            plugin
            for plugin in self.loadorder
            if plugin.name.lower() not in BASE_GAME_PLUGINS + AE_CC_PLUGINS
        ]

        return loadorder
