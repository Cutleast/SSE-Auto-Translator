"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import override

from core.plugin_interface.plugin import Plugin
from core.string import StringList

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
    @classmethod
    def can_be_in_bsas(cls) -> bool:
        return False

    @override
    def _extract_strings(self) -> StringList:
        return Plugin(self.full_path).extract_strings()
