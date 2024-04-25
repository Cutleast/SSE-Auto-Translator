"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import os
import qtpy.QtCore as qtc

import logging
import pickle
from pathlib import Path

import utilities as utils
from main import MainApp


class Cacher:
    """
    Class for managing cache data in SSE-AT/data/cache.
    """

    log = logging.getLogger("Cacher")

    __plugin_states_cache: dict[Path, tuple[bool, utils.Plugin.Status]] = {}
    """
    This cache is persistent
    and stores the states of the plugins of a modlist.
    """

    def __init__(self, app: MainApp):
        self.app = app

        self.path = app.cache_path

    def load_caches(self):
        """
        Loads available caches.
        """

        if self.path.is_dir():
            self.log.info("Loading caches...")

            plugin_states_cache_path = self.path / "plugin_states.cache"

            if plugin_states_cache_path.is_file():
                self.log.debug(
                    f"Loading Plugin States Cache from {str(plugin_states_cache_path)!r}..."
                )

                with plugin_states_cache_path.open("rb") as file:
                    cache: dict[Path, utils.Plugin.Status] = pickle.load(file)

                self.__plugin_states_cache = cache

                self.log.debug(
                    f"Loaded Plugin States for {len(self.__plugin_states_cache)} Plugin(s)."
                )

            self.log.info("Caches loaded.")

    def clear_plugin_states_cache(self):
        """
        Clears Plugin States Cache.
        """

        self.__plugin_states_cache.clear()

    def update_plugin_states_cache(self, modlist: list[utils.Mod]):
        """
        Updates Plugin States Cache from `modlist`.
        """

        plugins = [
            plugin
            for mod in modlist
            for plugin in mod.plugins
            if plugin.status != plugin.Status.NoneStatus
        ]

        cache = {
            plugin.path: (
                plugin.tree_item.checkState(0) == qtc.Qt.CheckState.Checked,
                plugin.status,
            )
            for plugin in plugins
        }

        self.__plugin_states_cache = cache

    def get_from_plugin_states_cache(self, plugin_path: Path):
        """
        Returns cached State for `plugin_path` if existing else None.
        """

        return self.__plugin_states_cache.get(plugin_path)

    def save_caches(self):
        """
        Saves non-empty caches.
        """

        self.log.info("Saving caches...")

        os.makedirs(self.path, exist_ok=True)

        if self.__plugin_states_cache:
            plugin_states_cache_path = self.path / "plugin_states.cache"

            self.log.debug(
                f"Saving Plugin States Cache to {str(plugin_states_cache_path)!r}..."
            )

            with plugin_states_cache_path.open("wb") as file:
                pickle.dump(self.__plugin_states_cache, file)

            self.log.debug(
                f"Saved Plugin States for {len(self.__plugin_states_cache)} Plugin(s)."
            )

        self.log.info("Caches saved.")
