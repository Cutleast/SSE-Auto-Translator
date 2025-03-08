"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import hashlib
import logging
import os
import pickle
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

import core.plugin_interface.plugin as plugin_interface
from core.database.string import String
from core.mod_instance.plugin import Plugin
from core.utilities.filesystem import get_file_identifier


class Cache:
    """
    Class for managing cache data in SSE-AT/data/cache.
    """

    log = logging.getLogger("Cache")

    __plugin_states_cache: dict[str, tuple[bool, Plugin.Status]] = {}
    """
    This cache is persistent
    and stores the states of the plugins of a modlist.
    """

    __plugin_strings_cache: dict[str, list[String]] = {}
    """
    This cache is persistent and stores extracted strings.
    """

    def __init__(self, cache_path: Path):
        self.path = cache_path

    def load_caches(self) -> None:
        """
        Loads available caches.
        """

        if self.path.is_dir():
            self.log.info("Loading caches...")

            plugin_states_cache_path = self.path / "plugin_states.cache"

            if plugin_states_cache_path.is_file():
                self.load_plugin_states_cache(plugin_states_cache_path)

            self.log.info("Caches loaded.")

    def clear_caches(self) -> None:
        """
        Clears all caches.
        """

        self.clear_plugin_states_cache()

        shutil.rmtree(self.path, ignore_errors=True)

    def get_plugin_strings(self, plugin_path: Path) -> list[String]:
        """
        Gets strings of `plugin_path` from cache or extracts them if not in cache.
        """

        strings: list[String]
        identifier: str = get_file_identifier(plugin_path)

        if identifier not in self.__plugin_strings_cache:
            cache_file: Path = self.path / "plugin_strings" / f"{identifier}.cache"

            if not cache_file.is_file():
                plugin = plugin_interface.Plugin(plugin_path)
                strings = plugin.extract_strings()
                os.makedirs(cache_file.parent, exist_ok=True)
                with cache_file.open(mode="wb") as data:
                    pickle.dump(strings, data)

                self.__plugin_strings_cache[identifier] = strings

                return strings

            with cache_file.open(mode="rb") as data:
                strings = pickle.load(data)

            self.__plugin_strings_cache[identifier] = strings

        strings = self.__plugin_strings_cache[identifier]

        self.log.debug(
            f"Loaded {len(strings)} string(s) for plugin {str(plugin_path)!r} from cache."
        )

        return strings

    def update_plugin_strings(self, plugin_path: Path, strings: list[String]) -> None:
        """
        Updates cached strings of `plugin_path`.
        """

        identifier = get_file_identifier(plugin_path)
        cache_file = self.path / "plugin_strings" / f"{identifier}.cache"

        os.makedirs(cache_file.parent, exist_ok=True)
        with cache_file.open(mode="wb") as data:
            pickle.dump(strings, data)

        self.log.debug(
            f"Updated {len(strings)} string(s) for plugin {str(plugin_path)!r}."
        )

    def clear_plugin_strings_cache(self) -> None:
        """
        Clears Plugin Strings Cache.
        """

        shutil.rmtree(self.path / "plugin_strings", ignore_errors=True)

    def load_plugin_states_cache(self, path: Path) -> None:
        self.log.debug(f"Loading Plugin States Cache from {str(path)!r}...")

        try:
            with path.open("rb") as file:
                cache: dict[str, tuple[bool, Plugin.Status]] = pickle.load(file)

            self.__plugin_states_cache = cache

            self.log.debug(
                f"Loaded Plugin States for {len(self.__plugin_states_cache)} Plugin(s)."
            )
        except Exception as ex:
            self.log.error(f"Failed to load plugin states cache: {ex}", exc_info=ex)

    def clear_plugin_states_cache(self) -> None:
        """
        Clears Plugin States Cache.
        """

        self.__plugin_states_cache.clear()

    def update_plugin_states_cache(self, plugin_states: dict[Plugin, bool]) -> None:
        """
        Updates Plugin States Cache from `modlist`.
        """

        cache = {
            get_file_identifier(plugin.path): (checked, plugin.status)
            for plugin, checked in plugin_states.items()
        }

        self.__plugin_states_cache = cache

    def get_from_plugin_states_cache(
        self, plugin_path: Path
    ) -> Optional[tuple[bool, Plugin.Status]]:
        """
        Returns cached State for `plugin_path` if existing else None.
        """

        return self.__plugin_states_cache.get(get_file_identifier(plugin_path))

    def save_plugin_states_cache(self, path: Path) -> None:
        self.log.debug(f"Saving Plugin States Cache to {str(path)!r}...")

        with path.open("wb") as file:
            pickle.dump(self.__plugin_states_cache, file)

        self.log.debug(
            f"Saved Plugin States for {len(self.__plugin_states_cache)} Plugin(s)."
        )

    def get_from_web_cache(
        self, url: str, max_age: int = 43200
    ) -> Optional[requests.Response]:
        """
        Returns cached Response for `url` if existing else None.

        Responses older than `max_age` are considered stale and deleted.

        TODO: Optimize the access time by caching them in-memory
        """

        response: Optional[requests.Response] = None

        request_id = hashlib.sha256(url.encode()).hexdigest()[:8]
        cache_file = self.path / "web_cache" / f"{request_id}.cache"

        if cache_file.is_file():
            with cache_file.open("rb") as file:
                _response: requests.Response = pickle.load(file)

            response_timestamp = datetime.strptime(
                _response.headers["Date"], "%a, %d %b %Y %H:%M:%S %Z"
            ).timestamp()

            if (time.time() - response_timestamp) < max_age:
                response = _response
            else:
                os.remove(cache_file)

        return response

    def add_to_web_cache(self, url: str, response: requests.Response) -> None:
        """
        Adds `response` to Web Cache for `url`.
        """

        request_id = hashlib.sha256(url.encode()).hexdigest()[:8]
        cache_file = self.path / "web_cache" / f"{request_id}.cache"

        os.makedirs(cache_file.parent, exist_ok=True)
        with cache_file.open("wb") as file:
            pickle.dump(response, file)

    def save_caches(self) -> None:
        """
        Saves non-empty caches.
        """

        self.log.info("Saving caches...")

        os.makedirs(self.path, exist_ok=True)

        if self.__plugin_states_cache:
            plugin_states_cache_path = self.path / "plugin_states.cache"

            self.save_plugin_states_cache(plugin_states_cache_path)

        self.log.info("Caches saved.")
