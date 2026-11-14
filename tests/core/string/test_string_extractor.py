"""
Copyright (c) Cutleast
"""

from pathlib import Path

import pytest

from core.mod_instance.mod import Mod
from core.mod_instance.mod_instance import ModInstance
from core.string.string_extractor import StringExtractor
from core.string.types import StringList
from core.utilities.game_language import GameLanguage
from tests.setup.data_factory import DataFactory

from ..core_test import CoreTest


class TestStringExtractor(CoreTest):
    """
    Tests `core.string.string_extractor.StringExtractor`.
    """

    def test_map_strings_from_mods(self) -> None:
        """
        Tests `StringExtractor.map_strings_from_mods()`.
        """

        # given
        original_mod: Mod = DataFactory.instance_mod("Wet and Cold SE")
        translation_mod: Mod = DataFactory.instance_mod("Wet and Cold SE - German")

        # when
        translation_strings: dict[Path, StringList] = (
            StringExtractor.map_strings_from_mods(translation_mod, original_mod)
        )

        # then
        assert translation_strings
        assert Path("WetandCold.esp") in translation_strings

    @pytest.mark.usefixtures("temp_folder_provider")
    def test_extract_strings_from_archive(self, data_folder: Path) -> None:
        """
        Tests `StringExtractor.extract_strings()` with a translation archive.
        """

        # given
        extractor = StringExtractor()
        mod_instance: ModInstance = DataFactory.mod_instance(
            [DataFactory.instance_mod("Wet and Cold SE")]
        )
        language: GameLanguage = GameLanguage.German
        test_file_path: Path = data_folder / "Wet and Cold SE - German.7z"

        # when
        imported_strings: dict[Path, StringList] = extractor.extract_strings(
            test_file_path, mod_instance, language
        )

        # then
        assert Path("wetandcold.esp") in imported_strings
        assert imported_strings[Path("wetandcold.esp")]
