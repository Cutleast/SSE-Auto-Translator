"""
Copyright (c) Cutleast
"""

from pathlib import Path

import pytest

from core.mod_instance.mod_instance import ModInstance
from core.mod_managers.modorganizer import ModOrganizer

from ..core_test import CoreTest


class TestModOrganizer(CoreTest):
    """
    Tests `core.mod_managers.modorganizer.ModOrganizer`.
    """

    def test_load_mod_instance(self) -> None:
        """
        Tests `core.mod_managers.modorganizer.ModOrganizer.load_mod_instance()`.
        """

        # given
        mo2 = ModOrganizer()
        instance_name: str = "Portable"
        instance_path: Path = self.data_path() / "mod_instance"

        # when
        mod_instance: ModInstance = mo2.load_mod_instance(
            instance_name, None, instance_path
        )

        # then
        assert mod_instance.display_name == "Portable"
        assert len(mod_instance.mods) == 7
        assert len(mod_instance.modfiles) == 8

    def test_load_mod_instance_fail(self) -> None:
        """
        Tests `core.mod_managers.modorganizer.ModOrganizer.load_mod_instance()`
        with invalid arguments.
        """

        # given
        mo2 = ModOrganizer()
        instance_name: str = "Portable"

        # when/then
        with pytest.raises(
            ValueError, match="instance_path is required for a portable instance!"
        ):
            mo2.load_mod_instance(instance_name)

    def test_get_instance_profiles(self) -> None:
        """
        Tests `core.mod_managers.modorganizer.ModOrganizer.get_instance_profiles()`.
        """

        # given
        mo2 = ModOrganizer()
        instance_name: str = "Portable"
        instance_path: Path = self.data_path() / "mod_instance"

        # when
        profiles: list[str] = mo2.get_instance_profiles(instance_name, instance_path)

        # then
        assert len(profiles) == 2
        assert "Default" in profiles
        assert "TestProfile" in profiles

    def test_get_instance_profiles_fail(self) -> None:
        """
        Tests `core.mod_managers.modorganizer.ModOrganizer.get_instance_profiles()`
        with invalid arguments.
        """

        # given
        mo2 = ModOrganizer()
        instance_name: str = "Portable"

        # when/then
        with pytest.raises(
            ValueError, match="instance_path is required for a portable instance!"
        ):
            mo2.get_instance_profiles(instance_name)
