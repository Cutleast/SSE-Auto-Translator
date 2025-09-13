"""
Copyright (c) Cutleast
"""

import logging

from core.string.plugin_string import PluginString
from tests.base_test import BaseTest


class CoreTest(BaseTest):
    """
    Base class for all core-related tests.
    """

    log: logging.Logger = logging.getLogger("CoreTest")

    @staticmethod
    def calc_unique_string_hash(string: PluginString) -> int:
        """
        Calculates a unique hash value from the specified string including all fields.

        Args:
            string (PluginString): The string to calculate the hash value from.

        Returns:
            int: The unique hash value.
        """

        return hash(
            (
                string.form_id,
                string.editor_id,
                string.type,
                string.original,
                string.index,
                string.string,
                string.status,
            )
        )
