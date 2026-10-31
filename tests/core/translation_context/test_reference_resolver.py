"""
Copyright (c) Cutleast
"""

from pathlib import Path

from core.file_types.plugin.string import PluginString
from core.translation_context.reference_resolver import (
    ReferenceResolver,
    ResolvedString,
)


class TestReferenceResolver:
    """
    Tests `core.translation_context.reference_resolver.ReferenceResolver`.
    """

    def test_get_record_id(self) -> None:
        """
        Tests that record IDs match the record IDs of plugin strings.
        """

        # given
        string = PluginString(
            form_id="0E000833|Elite Wolf Armor.esp", type="WEAP FULL", original="Bow"
        )

        # when
        own_record_id: str = ReferenceResolver.get_record_id(
            0x01000833, "Elite Wolf Armor.esp", ["Skyrim.esm"]
        )
        master_record_id: str = ReferenceResolver.get_record_id(
            0x000A2C94, "Elite Wolf Armor.esp", ["Skyrim.esm"]
        )

        # then
        assert own_record_id == string.record_id
        assert master_record_id == "0a2c94|skyrim.esm"

    def test_resolve_prefers_first_source(self) -> None:
        """
        Tests that strings from sources with a higher priority are preferred.
        """

        # given
        edited = PluginString(
            form_id="000A2C94|Skyrim.esm", type="NPC_ FULL", original="Lydia", string="A"
        )
        database = PluginString(
            form_id="010A2C94|Skyrim.esm", type="NPC_ FULL", original="Lydia", string="B"
        )
        other_type = PluginString(
            form_id="000A2C94|Skyrim.esm", type="NPC_ SHRT", original="Lydia"
        )
        resolver = ReferenceResolver(
            [
                {Path("Skyrim.esm"): [edited]},
                {Path("Skyrim.esm"): [database, other_type]},
            ]
        )

        # when
        resolved: list[ResolvedString] = resolver.resolve(
            "0a2c94|skyrim.esm", "NPC_ FULL"
        )

        # then
        assert resolved == [(edited, Path("Skyrim.esm"))]
