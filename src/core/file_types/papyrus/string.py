"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtWidgets import QApplication

from core.string.base_string import BaseString


class PapyrusString(BaseString):
    """
    Class for translation strings from Papyrus scripts (.pex).
    """

    def_line: str
    """The line, the string originates from."""

    line_id: int
    """The line number, the string originates from."""

    context: str
    """Additional context about the string."""

    key: str
    """A unique identifier for the string."""

    safety_score: int
    """The safety score of the string."""

    @property
    @override
    def id(self) -> str:
        return self.key

    @property
    @override
    def display_id(self) -> str:
        return self.key

    @override
    def get_localized_info(self) -> str:
        info: str = ""
        info += QApplication.translate("PapyrusString", "ID") + ": "
        info += self.key + "\n"
        info += QApplication.translate("PapyrusString", "Line") + ": "
        info += self.def_line + "\n"
        info += QApplication.translate("PapyrusString", "Line number") + ": "
        info += str(self.line_id) + "\n"
        info += QApplication.translate("PapyrusString", "Context") + ": "
        info += self.context + "\n"
        info += QApplication.translate("PapyrusString", "Safety score") + ": "
        info += str(self.safety_score) + "\n"

        return info.strip("\n")
