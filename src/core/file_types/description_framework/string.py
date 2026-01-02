"""
Copyright (c) Cutleast
"""

from typing import Optional, override

from PySide6.QtWidgets import QApplication

from core.string.base_string import BaseString


class DescriptionFwString(BaseString):
    """
    Class for strings from Description Framework files (data/*_DESC.ini).
    """

    string_id: str
    """Unique ID of the string consisting of a form id and plugin name."""

    priority: Optional[int] = None
    """An optional integer that specifies the override priority of the string."""

    @property
    @override
    def id(self) -> str:
        return self.string_id

    @property
    @override
    def display_id(self) -> str:
        display_id: str = self.string_id

        if self.priority is not None:
            display_id += f" - {self.priority}"

        return display_id

    @override
    def get_localized_info(self) -> str:
        # return f"ID: {self.string_id}"
        info: str = ""
        info += QApplication.translate("DescriptionFwString", "ID") + ": "
        info += self.string_id + "\n"

        if self.priority is not None:
            info += QApplication.translate("DescriptionFwString", "Priority") + ": "
            info += str(self.priority)

        return info.strip("\n")
