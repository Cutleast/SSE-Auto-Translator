"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import override

from core.database.string import String
from core.plugin_interface.plugin import Plugin

from .mod_file import ModFile


class PluginFile(ModFile):
    """
    Class for plugin files (*.esp, *.esm, *.esl).
    """

    @property
    @override
    def path(self) -> Path:
        return Path(self.name)

    @override
    @classmethod
    def get_glob_patterns(cls, language: str) -> list[str]:
        return [
            "*.esp",
            "*.esm",
            "*.esl",
        ]

    @override
    def _extract_strings(self) -> list[String]:
        return Plugin(self.full_path).extract_strings()
