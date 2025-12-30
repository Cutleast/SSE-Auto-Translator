"""
Copyright (c) Cutleast
"""

from pathlib import Path

import pytest
from mod_manager_lib.core.game_service import GameService
from mod_manager_lib.core.mod_manager.exceptions import InstanceNotFoundError
from mod_manager_lib.core.mod_manager.mod_manager import ModManager
from mod_manager_lib.core.mod_manager.modorganizer.mo2_instance_info import (
    MO2InstanceInfo,
)
from mod_manager_lib.core.mod_manager.vortex.profile_info import ProfileInfo

from core.mod_instance.mod_instance import ModInstance
from core.mod_instance.mod_instance_loader import ModInstanceLoader
from core.utilities.game_language import GameLanguage
from tests.core.core_test import CoreTest
from tests.setup.mock_plyvel import MockPlyvelDB


class TestModInstanceLoader(CoreTest):
    """
    Tests `core.mod_instance.mod_instance_loader.ModInstanceLoader`.
    """

    def test_load_portable_mo2_instance(
        self, mo2_instance_info: MO2InstanceInfo
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
        assert mod_instance.display_name == "Portable > Default"
        assert len(mod_instance.mods) == 8
        assert len(mod_instance.modfiles) == 10

    def test_load_global_mo2_instance(
        self, global_mo2_instance_info: MO2InstanceInfo
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
        assert mod_instance.display_name == "Test Instance > Default"
        assert len(mod_instance.mods) == 8
        assert len(mod_instance.modfiles) == 10

    def test_load_non_existing_mo2_instance(self, data_folder: Path) -> None:
        """
        Tests `ModInstanceLoader.load_instance()` with invalid arguments.
        """

        # given
        instance_data = MO2InstanceInfo(
            display_name="Something",
            game=GameService.get_game_by_id("skyrimse"),
            profile="Lol",
            is_global=False,
            base_folder=data_folder / "lol",
            mods_folder=data_folder / "lol" / "mods",
            profiles_folder=data_folder / "lol" / "profiles",
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
        assert len(mod_instance.modfiles) == 10

    def test_load_non_existing_vortex_profile(
        self, vortex_profile_info: ProfileInfo, vortex_db: MockPlyvelDB
    ) -> None:
        """
        Tests `ModInstanceLoader.load_instance()` with invalid arguments.
        """

        # given
        vortex_profile_info = ProfileInfo(
            display_name="Something",
            game=GameService.get_game_by_id("skyrimse"),
            id="lol",
            mod_manager=ModManager.Vortex,
        )
        loader = ModInstanceLoader()

        # when/then
        with pytest.raises(InstanceNotFoundError):
            loader.load_instance(vortex_profile_info, GameLanguage.German, True)
