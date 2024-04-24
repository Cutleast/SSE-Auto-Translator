"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging
import os
import pickle
from pathlib import Path

import utilities as utils
from plugin_parser import PluginParser


class StringExtractor:
    """
    Class for extracting Strings from Plugins.
    Caches extracted Strings to avoid obsolete Parsing.
    """

    cache: dict[str, list[utils.String]] = {}

    log = logging.getLogger("StringExtractor")

    def __init__(self):
        self.path = Path(".").resolve() / "data" / "cache" / "string_extractor.cache"

    def load_cache(self):
        """
        Loads cache if existing.
        """

        if self.path.is_file():
            self.log.info(f"Loading cache from {str(self.path)!r}...")

            with self.path.open("rb") as file:
                cache = pickle.load(file)

            self.cache = cache

            self.log.info(f"Loaded strings for {len(self.cache)} plugin(s) from cache.")

    def save_cache(self):
        """
        Saves cache.
        """

        if self.cache:
            self.log.info(f"Saving cache to {str(self.path)!r}...")

            os.makedirs(self.path.parent, exist_ok=True)

            with self.path.open("wb") as file:
                pickle.dump(self.cache, file)

            self.log.info(f"Saved strings for {len(self.cache)} plugin(s) to cache.")

    def extract_strings(self, plugin_path: Path, *args, **kwargs):
        """
        Extracts strings from `plugin_path` by getting it from cache or parsing the plugin.
        """

        key = str(plugin_path.resolve()).lower()

        if key not in self.cache:
            plugin_parser = PluginParser(plugin_path)
            strings = [
                string
                for group in plugin_parser.extract_strings(*args, **kwargs).values()
                for string in group
            ]
            self.cache[key] = strings

        return self.cache[key]


extractor = StringExtractor()
