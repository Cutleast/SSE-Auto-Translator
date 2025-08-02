"""
Copyright (c) Cutleast
"""

from core.string.plugin_string import PluginString
from core.string.string_status import StringStatus
from core.string.string_utils import StringUtils

from ..core_test import CoreTest


class TestStringUtils(CoreTest):
    """
    Tests `core.string.string_utils.StringUtils`.
    """

    def test_map_strings(self) -> None:
        """
        Tests `StringUtils.map_strings()`.
        """

        # given
        original_strings: list[PluginString] = [
            PluginString(
                original="Options: Obsidian Weathers",
                form_id="04000D65|Obsidian Weathers.esp",
                type="SPEL FULL",
                editor_id="ObsidianSpell",
            ),
            PluginString(
                original="Default",
                form_id="04000D62|Obsidian Weathers.esp",
                type="MESG ITXT",
                index=0,
                editor_id="ObsidianMessage",
            ),
            PluginString(
                original="Torch",
                form_id="0001D4EC|Skyrim.esm",
                type="LIGH FULL",
                editor_id="Torch01",
            ),
            PluginString(
                original="AnInternalName",
                form_id="00012345|Skyrim.esm",
                type="LIGH FULL",
                editor_id="Torch01",
                status=StringStatus.NoTranslationRequired,
            ),
            PluginString(
                original="An Unchanged String",
                form_id="00098765|Skyrim.esm",
                type="LIGH FULL",
                editor_id="Torch02",
            ),
        ]
        translation_strings: list[PluginString] = [
            PluginString(
                original="Optionen: Obsidian-Wetter",
                form_id="04000D65|Obsidian Weathers.esp",
                type="SPEL FULL",
                editor_id="ObsidianSpell",
            ),
            PluginString(
                original="Standard",
                form_id="04000D62|Obsidian Weathers.esp",
                type="MESG ITXT",
                index=0,
                editor_id="ObsidianMessage",
            ),
            PluginString(
                original="An Unchanged String",
                form_id="00098765|Skyrim.esm",
                type="LIGH FULL",
                editor_id="Torch02",
            ),
        ]

        # when
        merged_strings: list[PluginString] = StringUtils.map_strings(
            original_strings, translation_strings
        )

        # then
        assert merged_strings == [
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
            PluginString(
                original="Torch",
                form_id="0001D4EC|Skyrim.esm",
                type="LIGH FULL",
                editor_id="Torch01",
                status=StringStatus.TranslationRequired,
            ),
            PluginString(
                original="AnInternalName",
                string="AnInternalName",
                form_id="00012345|Skyrim.esm",
                type="LIGH FULL",
                editor_id="Torch01",
                status=StringStatus.NoTranslationRequired,
            ),
            PluginString(
                original="An Unchanged String",
                string="An Unchanged String",
                form_id="00098765|Skyrim.esm",
                type="LIGH FULL",
                editor_id="Torch02",
                status=StringStatus.NoTranslationRequired,
            ),
        ]
