"""
Copyright (c) Cutleast
"""

from abc import ABCMeta, abstractmethod
from typing import Optional

from core.database.string import String
from core.utilities.path import Path


class BaseCache(metaclass=ABCMeta):
    """
    Abstract base class for app cache.
    """

    @abstractmethod
    def get_strings_from_file_path(self, modfile_path: Path) -> Optional[list[String]]:
        """
        Returns cached strings of the specified mod file.

        Args:
            modfile_path (Path): Path to the mod file

        Returns:
            Optional[list[String]]: List of strings or None if the file is not cached
        """

    @abstractmethod
    def set_strings_for_file_path(
        self, modfile_path: Path, strings: list[String]
    ) -> None:
        """
        Sets cached strings for a mod file.

        Args:
            modfile_path (Path): Path to the mod file.
            strings (list[String]): List of strings from this file.
        """
