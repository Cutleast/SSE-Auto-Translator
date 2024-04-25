"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from pathlib import Path

import utilities as utils
from plugin_parser import PluginParser


class StringExtractor:
    """
    Class for extracting Strings from Plugins.
    Caches extracted Strings to avoid obsolete Parsing.
    """

    cache: dict[str, list[utils.String]] = {}

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
