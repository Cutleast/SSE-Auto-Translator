"""
Copyright (c) Cutleast
"""

from pathlib import Path

from core.config.user_config import UserConfig
from core.database.utilities import Utilities
from core.user_data.user_data import UserData

from ..core_test import CoreTest


class TestUtilities(CoreTest):
    """
    Tests `core.database.utilities.Utilities`.
    """

    def test_get_additional_files(self, data_folder: Path, user_data: UserData) -> None:
        """
        Tests `core.database.utilities.Utilities.get_additional_files()`.
        """

        # given
        utils = Utilities()
        user_config: UserConfig = user_data.user_config
        test_file_path: Path = data_folder / "Wet and Cold SE - German.7z"

        # when
        user_config.enable_interface_files = True
        user_config.enable_scripts = True
        user_config.enable_sound_files = True
        user_config.enable_textures = True
        additional_files: list[str] = utils.get_additional_files(
            test_file_path, self.tmp_folder(), user_config
        )

        # then
        assert additional_files == [
            "interface/translations/wetandcold_german.txt",
            "scripts/_wetquestscript.pex",
        ]

    def test_get_additional_files_from_bsa(self, user_data: UserData) -> None:
        """
        Tests `core.database.utilities.Utilities.get_additional_files_from_bsa()`.
        """

        # given
        utils = Utilities()
        user_config: UserConfig = user_data.user_config
        test_bsa_path: Path = (
            self.get_mod_by_name(
                "Ordinator - Perks of Skyrim", user_data.modinstance
            ).path
            / "Ordinator - Perks of Skyrim.bsa"
        )
        PATTERNS: dict[str, bool] = {
            f"**/interface/**/*_{user_config.language}.txt": user_config.enable_interface_files,
            "**/scripts/*.pex": True,
            "**/textures/**/*.dds": user_config.enable_textures,
            "**/textures/**/*.png": user_config.enable_textures,
            "**/sound/**/*.fuz": user_config.enable_sound_files,
            "**/sound/**/*.wav": user_config.enable_sound_files,
            "**/sound/**/*.lip": user_config.enable_sound_files,
        }

        # when
        additional_files: list[str] = list(
            map(
                lambda p: p.removeprefix(test_bsa_path.name + "\\").replace("\\", "/"),
                utils.get_additional_files_from_bsa(PATTERNS, test_bsa_path),
            )
        )

        # then
        assert "scripts/bladessparringscript.pex" in additional_files
        assert (
            "meshes/actors/character/facegendata/facegeom/ordinator - perks of skyrim.esp"
            not in additional_files
        )
