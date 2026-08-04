"""
Copyright (c) Cutleast
"""

from pathlib import Path

import pytest

from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.string.string_extractor import StringExtractor
from core.string.types import StringList
from core.user_data.user_data import UserData
from core.utilities.game_language import GameLanguage

from ..core_test import CoreTest


class TestStringExtractor(CoreTest):
    """
    Tests `core.string.string_extractor.StringExtractor`.
    """

    def test_map_strings_from_mods(self, user_data: UserData) -> None:
        """
        Tests `StringExtractor.map_strings_from_mods()`.
        """

        # given
        original_mod: Mod = self.get_mod_by_name(
            "Wet and Cold SE", user_data.mod_instance
        )
        translation_mod: Mod = self.get_mod_by_name(
            "Wet and Cold SE - German", user_data.mod_instance
        )

        # when
        translation_strings: dict[Path, StringList] = (
            StringExtractor.map_strings_from_mods(translation_mod, original_mod)
        )

        # then
        assert translation_strings
        assert Path("WetandCold.esp") in translation_strings

    # TODO: Fix this test
    @pytest.mark.skip("Conflict between fake filesystem and the 7-zip executable")
    def test_extract_strings_from_archive(
        self, data_folder: Path, user_data: UserData
    ) -> None:
        """
        Tests `StringExtractor.extract_strings_from_archive()`.
        """

        # given
        extractor = StringExtractor()
        mod_instance: ModInstance = user_data.mod_instance
        language: GameLanguage = user_data.user_config.language
        test_file_path: Path = data_folder / "Wet and Cold SE - German.7z"

        # when
        mod_instance.mods.remove(  # Remove mod so that it doesn't conflict with the imported mod
            self.get_mod_by_name("Wet and Cold SE - German", mod_instance)
        )
        imported_strings: dict[Path, StringList] = extractor.extract_strings(
            test_file_path, mod_instance, language
        )

        # then
        assert Path("wetandcold.esp") in imported_strings
        assert imported_strings[Path("wetandcold.esp")]
