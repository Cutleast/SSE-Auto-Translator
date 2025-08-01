"""
Copyright (c) Cutleast
"""

import pytest

from core.mod_instance.mod_instance import ModInstance
from core.mod_instance.mod_instance_loader import ModInstanceLoader
from core.mod_managers.exceptions import InstanceNotFoundError
from core.mod_managers.mod_manager import ModManager
from core.mod_managers.modorganizer.mo2_instance_info import Mo2InstanceInfo
from core.mod_managers.vortex.profile_info import ProfileInfo
from core.utilities.game_language import GameLanguage
from tests.core.core_test import CoreTest
from tests.core.setup.mock_plyvel import MockPlyvelDB


class TestModInstanceLoader(CoreTest):
    """
    Tests `core.mod_instance.mod_instance_loader.ModInstanceLoader`.
    """

    def test_load_portable_mo2_instance(
        self, mo2_instance_info: Mo2InstanceInfo
    ) -> None:
        """
        Tests `ModInstanceLoader.load_instance()` with a portable MO2 instance.
        """

        # given
        loader = ModInstanceLoader()

        # when
        mod_instance: ModInstance = loader.load_instance(
            mo2_instance_info, GameLanguage.German, True
        )

        # then
        assert mod_instance.display_name == "Portable"
        assert len(mod_instance.mods) == 7
        assert len(mod_instance.modfiles) == 8

    def test_load_global_mo2_instance(
        self, global_mo2_instance_info: Mo2InstanceInfo
    ) -> None:
        """
        Tests `ModInstanceLoader.load_instance()` with a global MO2 instance.
        """

        # given
        loader = ModInstanceLoader()

        # when
        mod_instance: ModInstance = loader.load_instance(
            global_mo2_instance_info, GameLanguage.German, True
        )

        # then
        assert mod_instance.display_name == "Test Instance"
        assert len(mod_instance.mods) == 7
        assert len(mod_instance.modfiles) == 8

    def test_load_non_existing_mo2_instance(self) -> None:
        """
        Tests `ModInstanceLoader.load_instance()` with invalid arguments.
        """

        # given
        instance_data = Mo2InstanceInfo(
            display_name="Something",
            profile="Lol",
            is_global=False,
            base_folder=self.data_path() / "lol",
            mods_folder=self.data_path() / "lol" / "mods",
            profiles_folder=self.data_path() / "lol" / "profiles",
            mod_manager=ModManager.ModOrganizer,
        )
        loader = ModInstanceLoader()

        # when/then
        with pytest.raises(InstanceNotFoundError):
            loader.load_instance(instance_data, GameLanguage.German, True)

    def test_load_vortex_profile(
        self, vortex_profile_info: ProfileInfo, vortex_db: MockPlyvelDB
    ) -> None:
        """
        Tests `ModInstanceLoader.load_instance()` with a Vortex profile.
        """

        # given
        loader = ModInstanceLoader()

        # when
        mod_instance: ModInstance = loader.load_instance(
            vortex_profile_info, GameLanguage.German, True
        )

        # then
        assert mod_instance.display_name == "Test Instance (1a2b3c4d)"
        assert len(mod_instance.mods) == 6
        assert len(mod_instance.modfiles) == 8

    def test_load_non_existing_vortex_profile(
        self, vortex_profile_info: ProfileInfo, vortex_db: MockPlyvelDB
    ) -> None:
        """
        Tests `ModInstanceLoader.load_instance()` with invalid arguments.
        """

        # given
        vortex_profile_info = ProfileInfo(
            display_name="Something", id="lol", mod_manager=ModManager.Vortex
        )
        loader = ModInstanceLoader()

        # when/then
        with pytest.raises(InstanceNotFoundError):
            loader.load_instance(vortex_profile_info, GameLanguage.German, True)
