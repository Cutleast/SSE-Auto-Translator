"""
Copyright (c) Cutleast
"""

from typing import Literal, override

from ..instance_info import InstanceInfo
from ..mod_manager import ModManager


class ProfileInfo(InstanceInfo):
    """
    Class for identifying an MO2 instance and profile.
    """

    id: str
    """The ID of the profile."""

    mod_manager: Literal[ModManager.Vortex]

    @override
    def get_mod_manager(self) -> ModManager:
        return self.mod_manager
