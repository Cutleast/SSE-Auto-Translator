"""
Copyright (c) Cutleast
"""

import logging

from core.string import String
from tests.base_test import BaseTest


class CoreTest(BaseTest):
    """
    Base class for all core-related tests.
    """

    log: logging.Logger = logging.getLogger("CoreTest")

    @staticmethod
    def calc_unique_string_hash(string: String) -> int:
        """
        Calculates a unique hash value from the specified string including all fields.

        Args:
            string (String): The string to calculate the hash value from.

        Returns:
            int: The unique hash value.
        """

        return hash((string.id, string.original, string.string, string.status))
