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
from typing import Optional

import requests

import core.plugin_interface.plugin as plugin_interface
from core.database.string import String
from core.mod_instance.mod_file import ModFile
from core.utilities.filesystem import get_file_identifier
from core.utilities.path import Path


class Cache:
    """
    Class for managing cache data in SSE-AT/data/cache.
    """

    log = logging.getLogger("Cache")

    __states_cache: dict[str, tuple[bool, ModFile.Status]] = {}
    """
    This cache is persistent and stores the states of the mod files of a modlist.
    """

    __strings_cache: dict[str, list[String]] = {}
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

            states_cache_path = self.path / "plugin_states.cache"

            if states_cache_path.is_file():
                self.load_states_cache(states_cache_path)

            self.log.info("Caches loaded.")

    def clear_caches(self) -> None:
        """
        Clears all caches.
        """

        self.clear_states_cache()

        shutil.rmtree(self.path, ignore_errors=True)

    def get_strings(self, modfile_path: Path) -> list[String]:
        """
        Returns cached strings of the specified mod file.

        Args:
            modfile_path (Path): Path to the mod file

        Returns:
            list[String]: List of strings
        """

        strings: list[String]
        identifier: str = get_file_identifier(modfile_path)

        if identifier not in self.__strings_cache:
            cache_file: Path = self.path / "plugin_strings" / f"{identifier}.cache"

            if not cache_file.is_file():
                plugin = plugin_interface.Plugin(modfile_path)
                strings = plugin.extract_strings()
                os.makedirs(cache_file.parent, exist_ok=True)
                with cache_file.open(mode="wb") as data:
                    pickle.dump(strings, data)

                self.__strings_cache[identifier] = strings

                return strings

            with cache_file.open(mode="rb") as data:
                strings = pickle.load(data)

            self.__strings_cache[identifier] = strings

        strings = self.__strings_cache[identifier]

        self.log.debug(
            f"Loaded {len(strings)} string(s) for mod file '{modfile_path}' from cache."
        )

        return strings

    def update_strings(self, modfile_path: Path, strings: list[String]) -> None:
        """
        Updates cached strings of `modfile_path`.
        """

        identifier = get_file_identifier(modfile_path)
        cache_file = self.path / "plugin_strings" / f"{identifier}.cache"

        os.makedirs(cache_file.parent, exist_ok=True)
        with cache_file.open(mode="wb") as data:
            pickle.dump(strings, data)

        self.log.debug(f"Updated {len(strings)} string(s) for plugin '{modfile_path}'.")

    def clear_strings_cache(self) -> None:
        """
        Clears Plugin Strings Cache.
        """

        shutil.rmtree(self.path / "plugin_strings", ignore_errors=True)

    def load_states_cache(self, path: Path) -> None:
        self.log.debug(f"Loading states Cache from '{path}'...")

        try:
            with path.open("rb") as file:
                cache: dict[str, tuple[bool, ModFile.Status]] = pickle.load(file)

            self.__states_cache = cache

            self.log.debug(f"Loaded states for {len(self.__states_cache)} mod file(s).")
        except Exception as ex:
            self.log.error(f"Failed to load states cache: {ex}", exc_info=ex)

    def clear_states_cache(self) -> None:
        """
        Clears states cache.
        """

        self.__states_cache.clear()

    def update_states_cache(self, states: dict[ModFile, bool]) -> None:
        """
        Updates cache from the specified mod file states.
        """

        cache = {
            get_file_identifier(modfile.path): (checked, modfile.status)
            for modfile, checked in states.items()
        }

        self.__states_cache = cache

    def get_from_states_cache(
        self, modfile_path: Path
    ) -> Optional[tuple[bool, ModFile.Status]]:
        """
        Returns cached state for `modfile_path` if existing else None.
        """

        return self.__states_cache.get(get_file_identifier(modfile_path))

    def save_states_cache(self, path: Path) -> None:
        self.log.debug(f"Saving states cache to '{path}'...")

        with path.open("wb") as file:
            pickle.dump(self.__states_cache, file)

        self.log.debug(f"Saved states for {len(self.__states_cache)} mod file(s).")

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

        if self.__states_cache:
            states_cache_path = self.path / "plugin_states.cache"

            self.save_states_cache(states_cache_path)

        self.log.info("Caches saved.")
