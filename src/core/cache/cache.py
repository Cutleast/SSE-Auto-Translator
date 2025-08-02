"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import hashlib
import os
import pickle
import shutil
import time
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Optional, override

import requests
from semantic_version import Version

from core.mod_file.translation_status import TranslationStatus
from core.string import StringList
from core.utilities.filesystem import get_file_identifier

from .base_cache import BaseCache


class Cache(BaseCache):
    """
    Class for managing cache data in SSE-AT/data/cache and cache utilities.
    """

    path: Path
    """
    Path to the cache folder.
    """

    __cache_version_file: Path
    """
    Path to the file containing the cache version.
    """

    __states_cache: dict[str, tuple[bool, TranslationStatus]] = {}
    """
    This cache is persistent and stores the states of the mod files of a modlist.
    """

    __states_cache_path: Path
    """
    Path to the cache file for the mod file states.
    """

    __strings_cache: dict[str, StringList] = {}
    """
    This cache is persistent and stores extracted strings.
    """

    __strings_cache_path: Path
    """
    Path to the folder for the strings cache files.
    """

    def __init__(self, cache_path: Path, app_version: str) -> None:
        self.path = cache_path
        self.__cache_version_file = self.path / "version"
        self.__states_cache_path = self.path / "modfile_states.cache"
        self.__strings_cache_path = self.path / "modfile_strings"

        self.path.mkdir(parents=True, exist_ok=True)

        if self.__cache_version_file.is_file():
            cache_version: str = self.__cache_version_file.read_text().strip()

            if app_version != "development" and Version(cache_version) < Version(
                app_version
            ):
                self.clear_caches()
                self.path.mkdir(parents=True)
                self.log.info("Cleared caches due to outdated cache version.")

        elif os.listdir(self.path):
            self.clear_caches()
            self.path.mkdir(parents=True)
            self.log.info("Cleared caches due to missing cache version file.")

        self.__cache_version_file.write_text(app_version)

    def load_caches(self) -> None:
        """
        Loads available caches.
        """

        if self.path.is_dir():
            self.log.info("Loading caches...")

            if self.__states_cache_path.is_file():
                self.load_states_cache(self.__states_cache_path)

            self.log.info("Caches loaded.")

    def clear_caches(self) -> None:
        """
        Clears all caches.
        """

        self.clear_states_cache()
        shutil.rmtree(self.path, ignore_errors=True)

        self.log.info("Caches cleared.")

    @override
    def get_strings_from_file_path(self, modfile_path: Path) -> Optional[StringList]:
        strings: Optional[StringList]
        identifier: str = get_file_identifier(modfile_path)

        if identifier not in self.__strings_cache:
            cache_file: Path = self.__strings_cache_path / f"{identifier}.cache"

            if cache_file.is_file():
                with cache_file.open(mode="rb") as data:
                    cached_strings: StringList = pickle.load(data)

                self.__strings_cache[identifier] = cached_strings

        strings = self.__strings_cache.get(identifier)

        if strings is not None:
            self.log.debug(
                f"Loaded {len(strings)} string(s) for mod file '{modfile_path}' from cache."
            )
        else:
            self.log.debug(f"Strings for mod file '{modfile_path}' are not in cache.")

        return strings

    @override
    def set_strings_for_file_path(
        self, modfile_path: Path, strings: StringList
    ) -> None:
        identifier: str = get_file_identifier(modfile_path)
        cache_file: Path = self.__strings_cache_path / f"{identifier}.cache"

        os.makedirs(cache_file.parent, exist_ok=True)
        with cache_file.open(mode="wb") as data:
            pickle.dump(strings, data)

        self.log.debug(
            f"Updated {len(strings)} string(s) for mod file '{modfile_path}'."
        )

    def clear_strings_cache(self) -> None:
        """
        Clears mod file strings cache.
        """

        shutil.rmtree(self.__strings_cache_path, ignore_errors=True)

    def load_states_cache(self, path: Path) -> None:
        self.log.debug(f"Loading states cache from '{path}'...")

        try:
            with path.open("rb") as file:
                cache: dict[str, tuple[bool, TranslationStatus]] = pickle.load(file)

            self.__states_cache = cache

            self.log.debug(f"Loaded states for {len(self.__states_cache)} mod file(s).")
        except Exception as ex:
            self.log.error(f"Failed to load states cache: {ex}", exc_info=ex)

    def clear_states_cache(self) -> None:
        """
        Clears states cache.
        """

        self.__states_cache.clear()

    def update_states_cache(
        self, states: dict[Path, tuple[bool, TranslationStatus]]
    ) -> None:
        """
        Updates cache from the specified mod file states.
        """

        cache: dict[str, tuple[bool, TranslationStatus]] = {
            get_file_identifier(file): (checked, status)
            for file, (checked, status) in states.items()
        }

        self.__states_cache = cache

    def get_from_states_cache(
        self, modfile_path: Path
    ) -> Optional[tuple[bool, TranslationStatus]]:
        """
        Returns cached state for `modfile_path` if existing else None.
        """

        return self.__states_cache.get(get_file_identifier(modfile_path))

    def save_states_cache(self, path: Path) -> None:
        self.log.debug(f"Saving states cache to '{path}'...")

        with path.open("wb") as file:
            pickle.dump(self.__states_cache, file)

        self.log.debug(f"Saved states for {len(self.__states_cache)} mod file(s).")

    @lru_cache
    def get_from_web_cache(
        self, url: str, max_age: int = 43200
    ) -> Optional[requests.Response]:
        """
        Returns cached Response for `url` if existing else None.

        Responses older than `max_age` are considered stale and deleted.
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
            self.save_states_cache(self.__states_cache_path)

        self.log.info("Caches saved.")
