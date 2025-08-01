"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Literal, override

from ..instance_info import InstanceInfo
from ..mod_manager import ModManager


class Mo2InstanceInfo(InstanceInfo):
    """
    Class for identifying an MO2 instance and profile.
    """

    profile: str
    """The selected profile of the instance."""

    is_global: bool
    """Whether the instance is a global or portable instance."""

    base_folder: Path
    """
    Path to the base directory of the instance.
    **The folder must contain the instance's ModOrganizer.ini file!**
    """

    mods_folder: Path
    """Path to the instance's "mods" folder."""

    profiles_folder: Path
    """Path to the instance's "profiles" folder."""

    mod_manager: Literal[ModManager.ModOrganizer]

    @override
    def get_mod_manager(self) -> ModManager:
        return self.mod_manager
