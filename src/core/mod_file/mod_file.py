"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, override

from app_context import AppContext
from core.cache.base_cache import BaseCache
from core.string.string import String
from core.utilities.filesystem import relative_data_path

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

    full_path: Path
    """
    The full path to the file in its mod instance.
    """

    status: TranslationStatus = TranslationStatus.NoneStatus
    """
    Translation status of this file.
    """

    @property
    def path(self) -> Path:
        """
        Path of this file, relative to the game's "Data" folder.
        """

        return Path(relative_data_path(str(self.full_path)))

    @override
    def __hash__(self) -> int:
        return hash((self.name.lower(), str(self.full_path).lower()))

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

    @classmethod
    @abstractmethod
    def can_be_in_bsas(cls) -> bool:
        """
        Returns whether this file type can occur in BSA archives.

        Returns:
            bool: Whether this file type can occur in BSA archives.
        """

    def get_strings(self) -> list[String]:
        """
        Extracts and returns all strings from this file. Uses the current app's cache, if
        available.

        Returns:
            list[String]: List of all strings from this file.
        """

        cache: Optional[BaseCache] = AppContext.get_cache()
        strings: Optional[list[String]] = None

        if cache is not None:
            strings = cache.get_strings_from_file_path(self.full_path)

        if strings is None:
            strings = self._extract_strings()

            if cache is not None:
                cache.set_strings_for_file_path(self.full_path, strings)

        return strings

    @abstractmethod
    def _extract_strings(self) -> list[String]:
        """
        Extracts and returns all strings from this file.

        Returns:
            list[String]: List of all strings from this file.
        """
