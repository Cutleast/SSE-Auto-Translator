"""
Copyright (c) Cutleast
"""

from typing import override

from core.string.base_string import BaseString


class BestiaryString(BaseString):
    """
    Model for strings from Dragonborn's Bestiary files.
    """

    bestiary_id: str
    """Field for identifying uniquely identifying this string for a creature."""

    @property
    @override
    def id(self) -> str:
        return self.bestiary_id

    @property
    @override
    def display_id(self) -> str:
        return self.bestiary_id

    @override
    def get_localized_info(self) -> str:
        return f"Bestiary ID: {self.bestiary_id}"
