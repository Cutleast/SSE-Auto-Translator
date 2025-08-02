"""
Copyright (c) Cutleast
"""

from collections.abc import Iterable

from core.utilities.container_utils import unique

from . import String, StringList


class StringUtils:
    """
    Class with various utility methods for strings.
    """

    @staticmethod
    def unique(strings: Iterable[String]) -> StringList:
        """
        Removes duplicates from an iterable of strings. Unique strings are identified by
        `String.id`.

        Convenience method for
            `unique(strings, key=lambda s: s.id)`.

        Args:
            strings (Iterable[String]): Iterable with duplicate strings.

        Returns:
            List of strings without duplicates.
        """

        return unique(strings, key=lambda s: s.id)
