"""
Copyright (c) Cutleast
"""

from pathlib import Path

import pytest

from core.plugin_interface.plugin import Plugin
from core.string.plugin_string import PluginString
from core.string.string_status import StringStatus

from ..core_test import CoreTest


class TestPlugin(CoreTest):
    """
    Tests `core.plugin_interface.plugin.Plugin`.
    """

    EXTRACT_STRINGS_DATA: list[tuple[Path, list[PluginString], int]] = [
        (
            Path("Obsidian Weathers and Seasons") / "Obsidian Weathers.esp",
            [
                PluginString(
                    form_id="04000D65|Obsidian Weathers.esp",
                    editor_id="ObsidianSpell",
                    type="SPEL FULL",
                    original="Options: Obsidian Weathers",
                    status=StringStatus.TranslationRequired,
                ),
                PluginString(
                    form_id="04000D65|Obsidian Weathers.esp",
                    type="SPEL DESC",
                    original="Options provided by Obsidian Weathers",
                    editor_id="ObsidianSpell",
                    status=StringStatus.TranslationRequired,
                ),
                PluginString(
                    form_id="000703C2|Skyrim.esm",
                    type="REGN RDMP",
                    original="Windhelm",
                    editor_id="WeatherWindhelm",
                    status=StringStatus.TranslationRequired,
                ),
                PluginString(
                    form_id="0000003C|Skyrim.esm",
                    type="WRLD FULL",
                    original="Skyrim",
                    editor_id="Tamriel",
                    status=StringStatus.TranslationRequired,
                ),
                PluginString(
                    form_id="04000D62|Obsidian Weathers.esp",
                    type="MESG ITXT",
                    original="Default",
                    index=0,
                    editor_id="ObsidianMessage",
                    status=StringStatus.TranslationRequired,
                ),
                PluginString(
                    form_id="04000D62|Obsidian Weathers.esp",
                    type="MESG ITXT",
                    original="Natural",
                    index=1,
                    editor_id="ObsidianMessage",
                    status=StringStatus.TranslationRequired,
                ),
                PluginString(
                    form_id="04000D62|Obsidian Weathers.esp",
                    type="MESG DESC",
                    original="Filters",
                    editor_id="ObsidianMessage",
                    status=StringStatus.TranslationRequired,
                ),
            ],
            29,
        ),
        (
            Path("Ordinator - Perks of Skyrim") / "Ordinator - Perks of Skyrim.esp",
            [
                PluginString(
                    form_id="030A653C|Ordinator - Perks of Skyrim.esp",
                    type="RACE FULL",
                    original="Mind Spider",
                    editor_id="ORD_Ill_MindSpiders_Race",
                    status=StringStatus.TranslationRequired,
                ),
                PluginString(
                    form_id="03007513|Ordinator - Perks of Skyrim.esp",
                    type="MGEF FULL",
                    original="Thieving Raven",
                    editor_id="ORD_Arc_ArcheryOnHit_Effect_ThievingRaven",
                    status=StringStatus.TranslationRequired,
                ),
                PluginString(
                    form_id="03008032|Ordinator - Perks of Skyrim.esp",
                    type="MGEF DNAM",
                    original="Revenge is a bitter drink.",
                    editor_id="ORD_Hea_ReapTheWhirlwind_Effect_Proc",
                    status=StringStatus.TranslationRequired,
                ),
                PluginString(
                    form_id="03034DEC|Ordinator - Perks of Skyrim.esp",
                    type="PERK FULL",
                    original="Lockdown",
                    editor_id="ORD_Loc30_Lockdown_Perk_30_OrdASISExclude",
                    status=StringStatus.TranslationRequired,
                ),
                PluginString(
                    form_id="030358D3|Ordinator - Perks of Skyrim.esp",
                    type="PERK EPF2",
                    original="Hotwire",
                    index=0,
                    editor_id="ORD_Loc50_Hotwire_Perk_50_OrdASISExclude",
                    status=StringStatus.TranslationRequired,
                ),
                PluginString(
                    form_id="03035E3F|Ordinator - Perks of Skyrim.esp",
                    type="PERK DESC",
                    original=(
                        "Performing a silent roll makes you ethereal for 1 second, "
                        "causing all incoming attacks and spells to miss."
                    ),
                    editor_id="ORD_Sne60_DodgeRoll_Perk_60",
                    status=StringStatus.TranslationRequired,
                ),
                PluginString(
                    form_id="00000453|Skyrim.esm",
                    type="AVIF FULL",
                    original="Pickpocket",
                    editor_id="AVPickpocket",
                    status=StringStatus.TranslationRequired,
                ),
                PluginString(
                    form_id="00000456|Skyrim.esm",
                    type="AVIF DESC",
                    original=(
                        "An alchemist can create magical potions and deadly poisons."
                    ),
                    editor_id="AVAlchemy",
                    status=StringStatus.TranslationRequired,
                ),
            ],
            5165,
        ),
    ]
    """Test data for `Plugin.extract_strings()`."""

    @pytest.mark.parametrize(
        "plugin_file, expected_strings, expected_num_strings", EXTRACT_STRINGS_DATA
    )
    def test_extract_strings(
        self,
        plugin_file: Path,
        expected_strings: list[PluginString],
        expected_num_strings: int,
    ) -> None:
        """
        Tests `Plugin.extract_strings()`.

        Args:
            plugin_file (Path):
                Path to the plugin file, relative to the test mod instance's mods folder.
            expected_strings (list[PluginString]):
                List of strings that are expected to be extracted. This list is not
                exclusive.
            expected_num_strings (int):
                Number of strings that are expected to be extracted.
        """

        # given
        plugin_file = self.data_path() / "mod_instance" / "mods" / plugin_file

        # when
        actual_strings: list[PluginString] = Plugin(plugin_file).extract_strings()

        # then
        assert len(actual_strings) == expected_num_strings
        actual_hashes: list[int] = [
            CoreTest.calc_unique_string_hash(string) for string in actual_strings
        ]
        for string in expected_strings:
            assert CoreTest.calc_unique_string_hash(string) in actual_hashes, (
                f"{string} is missing!"
            )
