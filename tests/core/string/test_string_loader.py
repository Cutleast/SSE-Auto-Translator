"""
Copyright (c) Cutleast
"""

from pathlib import Path

from core.file_types.plugin.string import PluginString
from core.string.string_loader import StringLoader
from core.string.string_status import StringStatus
from core.string.types import StringList

from ..core_test import CoreTest


class TestStringLoader(CoreTest):
    """
    Tests `core.string.string_loader.StringLoader`.
    """

    def test_load_strings_from_legacy_file(self, data_folder: Path) -> None:
        """
        Tests the deserialization and loading of strings from a legacy .ats file.
        """

        # given
        legacy_ats_file_path: Path = (
            data_folder
            / "translations"
            / "Obsidian Weathers and Seasons - German"
            / "obsidian weathers.esp.ats"
        )
        expected_strings: StringList = [
            PluginString(
                form_id="04000D65|Obsidian Weathers.esp",
                type="SPEL FULL",
                original="Options: Obsidian Weathers",
                string="Optionen: Obsidian-Wetter",
                editor_id="ObsidianSpell",
                status=StringStatus.TranslationComplete,
            ),
            PluginString(
                form_id="04000D62|Obsidian Weathers.esp",
                type="MESG ITXT",
                original="Default",
                string="Standard",
                index=0,
                editor_id="ObsidianMessage",
                status=StringStatus.TranslationComplete,
            ),
        ]

        # when
        actual_strings: StringList = StringLoader.load_strings_from_legacy_file(
            legacy_ats_file_path
        )

        # then
        assert len(actual_strings) == 29
        actual_hashes: list[int] = [
            CoreTest.calc_unique_string_hash(string) for string in actual_strings
        ]
        for string in expected_strings:
            assert CoreTest.calc_unique_string_hash(string) in actual_hashes, (
                f"{string} is missing!"
            )

    def test_load_strings_from_json_file(self, data_folder: Path) -> None:
        """
        Tests the deserialization and loading of strings from a JSON file.
        """

        # given
        json_file_path: Path = (
            data_folder
            / "translations"
            / "Obsidian Weathers and Seasons - German"
            / "obsidian weathers.esp.json"
        )
        expected_strings: StringList = [
            PluginString(
                form_id="04000D65|Obsidian Weathers.esp",
                type="SPEL FULL",
                original="Options: Obsidian Weathers",
                string="Optionen: Obsidian-Wetter",
                editor_id="ObsidianSpell",
                status=StringStatus.TranslationComplete,
            ),
            PluginString(
                form_id="04000D62|Obsidian Weathers.esp",
                type="MESG ITXT",
                original="Default",
                string="Standard",
                index=0,
                editor_id="ObsidianMessage",
                status=StringStatus.TranslationComplete,
            ),
        ]

        # when
        actual_strings: StringList = StringLoader.load_strings_from_json_file(
            json_file_path
        )

        # then
        assert len(actual_strings) == 29
        actual_hashes: list[int] = [
            CoreTest.calc_unique_string_hash(string) for string in actual_strings
        ]
        for string in expected_strings:
            assert CoreTest.calc_unique_string_hash(string) in actual_hashes, (
                f"{string} is missing!"
            )
