"""
Copyright (c) Cutleast
"""

from typing import override

from .base_string import BaseString


class InterfaceString(BaseString):
    """
    Class for translation strings from interface translation files
    (data/interface/translations/*_<language>.txt).
    """

    mcm_id: str
    """Unique MCM ID of the string."""

    @property
    @override
    def id(self) -> str:
        return self.mcm_id

    @property
    @override
    def display_id(self) -> str:
        return self.mcm_id

    @override
    def get_localized_info(self) -> str:
        return f"ID: {self.mcm_id}"
