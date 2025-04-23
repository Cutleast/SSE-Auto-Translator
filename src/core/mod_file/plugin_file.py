"""
Copyright (c) Cutleast
"""

from typing import override

from core.cache.base_cache import BaseCache
from core.database.string import String
from core.plugin_interface.plugin import Plugin
from core.utilities.filesystem import get_file_identifier
from core.utilities.path import Path

from .mod_file import ModFile


class PluginFile(ModFile):
    """
    Class for plugin files (*.esp, *.esm, *.esl).
    """

    @override
    @classmethod
    def get_glob_patterns(cls, language: str) -> list[str]:
        return [
            "*.esp",
            "*.esm",
            "*.esl",
        ]

    @override
    @BaseCache.persistent_cache(
        cache_subfolder=Path("plugin_strings"),
        id_generator=lambda self: get_file_identifier(self.path),
    )
    def _extract_strings(self) -> list[String]:
        return Plugin(self.path).extract_strings()
