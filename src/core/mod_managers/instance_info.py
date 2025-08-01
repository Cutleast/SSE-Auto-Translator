"""
Copyright (c) Cutleast
"""

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from .mod_manager import ModManager


class InstanceInfo(BaseModel, metaclass=ABCMeta):
    """
    Base class for identifying an instance within a mod manager.
    """

    display_name: str
    """The display name of the instance."""

    @abstractmethod
    def get_mod_manager(self) -> "ModManager":
        """
        Returns the mod manager that manages this instance.

        Returns:
            ModManager: The mod manager that manages this instance.
        """
