"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, override

from core.cache.base_cache import BaseCache
from core.database.string import String

from .translation_status import TranslationStatus


@dataclass
class ModFile(metaclass=ABCMeta):
    """
    Dataclass for translatable mod files.
    """

    name: str
    """
    The filename of this file.
    """

    path: Path
    """
    The full path to the file in its mod instance.
    """

    status: TranslationStatus = TranslationStatus.NoneStatus
    """
    Translation status of this file.
    """

    @override
    def __hash__(self) -> int:
        return hash((self.name.lower(), str(self.path).lower()))

    @classmethod
    @abstractmethod
    def get_glob_patterns(cls, language: str) -> list[str]:
        """
        Returns the glob patterns for this file type.

        Args:
            language (str):
                Language to filter for (esp. relevant for interface translation files)

        Returns:
            list[str]: List of glob patterns
        """

    def get_strings(self, cache: Optional[BaseCache] = None) -> list[String]:
        """
        Extracts and returns all strings from this file.
        This method uses the specified cache if available.

        Args:
            cache (Optional[BaseCache], optional): Cache to use. Defaults to None.

        Returns:
            list[String]: List of all strings from this file.
        """

        strings: Optional[list[String]] = None

        if cache is not None:
            strings = cache.get_strings_from_file_path(self.path)

        if strings is None:
            strings = self._extract_strings()

            if cache is not None:
                cache.set_strings_for_file_path(self.path, strings)

        return strings

    @abstractmethod
    def _extract_strings(self) -> list[String]:
        """
        Extracts and returns all strings from this file.

        Returns:
            list[String]: List of all strings from this file.
        """
