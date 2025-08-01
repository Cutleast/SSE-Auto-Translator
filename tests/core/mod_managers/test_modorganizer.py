"""
Copyright (c) Cutleast
"""

from pathlib import Path

from core.mod_managers.modorganizer.modorganizer_api import ModOrganizerApi

from ..core_test import CoreTest


class TestModOrganizer(CoreTest):
    """
    Tests `core.mod_managers.modorganizer.ModOrganizer`.
    """

    def test_get_instance_profiles(self) -> None:
        """
        Tests `core.mod_managers.modorganizer.ModOrganizer.get_instance_profiles()`.
        """

        # given
        mo2 = ModOrganizerApi()
        mo2_ini_path: Path = self.data_path() / "mod_instance" / "ModOrganizer.ini"

        # when
        profiles: list[str] = mo2.get_profile_names(mo2_ini_path)

        # then
        assert len(profiles) == 2
        assert "Default" in profiles
        assert "TestProfile" in profiles
