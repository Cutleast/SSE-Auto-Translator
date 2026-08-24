"""
Copyright (c) Cutleast
"""

from abc import abstractmethod
from typing import Optional

from cutleast_core_lib.core.utilities.localized_enum import BaseEnum
from PySide6.QtGui import QColor


class ColoredEnum(BaseEnum):
    """
    Enum with assigned colors.
    """

    @abstractmethod
    def get_base_color(self) -> Optional[QColor]:
        """
        Returns:
            Optional[QColor]: Base color for this enum member.
        """

    @abstractmethod
    def get_bg_color(self) -> Optional[QColor]:
        """
        Returns:
            Optional[QColor]: Background color for this enum member.
        """

    @abstractmethod
    def get_highlighted_bg_color(self) -> Optional[QColor]:
        """
        Returns:
            Optional[QColor]: Highlighted background color for this enum member.
        """

    @abstractmethod
    def get_fg_color(self) -> Optional[QColor]:
        """
        Returns:
            Optional[QColor]: Foreground color for this enum member.
        """
