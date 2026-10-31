"""
Copyright (c) Cutleast
"""

from pathlib import Path
from struct import pack
from typing import cast

from bethkit import Game, PluginWriter, WritableGroup, WritableRecord

from core.file_types.plugin.file import PluginFile
from core.file_types.plugin.string import PluginString
from core.mod_file.context import ModFileContext
from core.string.types import String, StringList
from tests.base_test import BaseTest


class TestPluginFile(BaseTest):
    """
    Tests `core.file_types.plugin.file.PluginFile`.
    """

    def test_extract_strings(self, data_folder: Path) -> None:
        """
        Tests extracting addressed strings through Bethkit's schema.
        """

        # given
        plugin_path: Path = data_folder / "esp2dsd" / "orig" / "WetandCold.esp"
        plugin_file = PluginFile(name=plugin_path.name, full_path=plugin_path)

        # when
        strings: StringList = plugin_file.get_strings()

        # then
        assert len(strings) == 204
        assert all(isinstance(string, PluginString) for string in strings)
        assert len({string.id for string in strings}) == len(strings)

    def test_dump_strings(self, data_folder: Path) -> None:
        """
        Tests replacing a serialized string using its stable application ID.
        """

        # given
        plugin_path: Path = data_folder / "esp2dsd" / "orig" / "WetandCold.esp"
        plugin_file = PluginFile(name=plugin_path.name, full_path=plugin_path)
        strings: StringList = plugin_file.get_strings()
        string: PluginString = next(
            item
            for item in strings
            if isinstance(item, PluginString) and item.type == "MGEF FULL"
        )
        replacement: str = "Bethkit migration test"
        string.string = replacement
        strings = [
            PluginString.model_validate_json(item.model_dump_json()) for item in strings
        ]
        output_folder: Path = self.tmp_folder() / "bethkit-plugin-output"
        output_folder.mkdir(parents=True, exist_ok=True)

        # when
        plugin_file.dump_strings(strings, output_folder, use_dsd_format=False)
        output_plugin = PluginFile(
            name=plugin_path.name, full_path=output_folder / plugin_path.name
        )
        output_strings: StringList = output_plugin.get_strings()

        # then
        output_string: PluginString = next(
            item
            for item in output_strings
            if isinstance(item, PluginString) and item.id == string.id
        )
        assert output_string.original == replacement

    def test_original_and_translation_ids(self, data_folder: Path) -> None:
        """
        Tests ID stability between a real plugin and its direct translation.
        """

        # given
        original_path: Path = data_folder / "esp2dsd" / "orig" / "WetandCold.esp"
        translated_path: Path = data_folder / "esp2dsd" / "trans" / "WetandCold.esp"
        original = PluginFile(name=original_path.name, full_path=original_path)
        translated = PluginFile(name=translated_path.name, full_path=translated_path)

        # when
        original_strings: StringList = original.get_strings()
        translated_strings: StringList = translated.get_strings()

        # then
        assert {string.id for string in original_strings} == {
            string.id for string in translated_strings
        }

    @staticmethod
    def __write_quest(
        path: Path,
        stages: list[int],
        *,
        reverse_entries: bool = False,
        conditional: bool = True,
    ) -> None:
        """
        Creates a quest with two journal entries per stage.

        Args:
            path (Path): Destination plugin.
            stages (list[int]): Stage numbers in their source order.
            reverse_entries (bool, optional): Reverse the entries. Defaults to False.
            conditional (bool, optional): Add distinct conditions. Defaults to True.
        """

        with (
            PluginWriter(Game.SKYRIM_SE) as writer,
            WritableGroup.new("QUST") as group,
            WritableRecord.new("QUST", form_id=0x1234) as record,
        ):
            record.add_subrecord("EDID", b"TestQuest\0")
            for stage in stages:
                record.add_subrecord("INDX", stage.to_bytes(2, "little") + b"\0\0")
                for entry in [1, 0] if reverse_entries else [0, 1]:
                    record.add_subrecord("QSDT", b"\0")
                    if conditional:
                        record.add_subrecord(
                            "CTDA", bytes(4) + pack("<f", stage * 2 + entry) + bytes(24)
                        )
                    record.add_subrecord(
                        "CNAM", f"Stage {stage} entry {entry}\0".encode()
                    )

            group.add_record(record)
            writer.add_group(group)
            path.write_bytes(writer.write_to_bytes())

    def test_quest_export_after_stage_insertion(self, tmp_path: Path) -> None:
        """
        Tests journal export after inserting a stage and reversing its entries.
        """

        # given
        plugin_path: Path = tmp_path / "Quest.esp"
        TestPluginFile.__write_quest(plugin_path, [10])
        plugin_file = PluginFile(name=plugin_path.name, full_path=plugin_path)
        strings: StringList = [
            PluginString.model_validate_json(string.model_dump_json())
            for string in plugin_file.get_strings()
        ]
        strings[0].string = "Erster Eintrag"
        strings[1].string = "Zweiter Eintrag"
        TestPluginFile.__write_quest(plugin_path, [20, 10], reverse_entries=True)
        output_folder: Path = tmp_path / "translated"

        # when
        plugin_file.dump_strings(strings, output_folder, use_dsd_format=False)
        output_plugin = PluginFile(
            name=plugin_path.name, full_path=output_folder / plugin_path.name
        )
        output_strings: StringList = output_plugin.get_strings()

        # then
        assert [string.original for string in output_strings] == [
            "Stage 20 entry 1",
            "Stage 20 entry 0",
            "Zweiter Eintrag",
            "Erster Eintrag",
        ]
        assert [string.id for string in output_strings[2:]] == [
            string.id for string in reversed(strings)
        ]

    def test_identical_journal_entries_are_distinguished(self, tmp_path: Path) -> None:
        """
        Tests extracting entries that stage and conditions alone cannot distinguish.
        """

        # given
        plugin_path: Path = tmp_path / "Identical.esp"
        TestPluginFile.__write_quest(plugin_path, [10, 20], conditional=False)
        plugin_file = PluginFile(name=plugin_path.name, full_path=plugin_path)

        # when
        strings: StringList = plugin_file.get_strings()

        # then
        assert len({string.id for string in strings}) == 4

    def test_invisible_string_types_are_ignored(self, tmp_path: Path) -> None:
        """
        Tests skipping rank titles and body part names, which are not shown in-game.
        """

        # given
        plugin_path: Path = tmp_path / "Invisible.esp"
        with (
            PluginWriter(Game.SKYRIM_SE) as writer,
            WritableGroup.new("FACT") as faction_group,
            WritableRecord.new("FACT", form_id=0x1234) as faction,
            WritableGroup.new("BPTD") as body_part_group,
            WritableRecord.new("BPTD", form_id=0x1235) as body_part,
        ):
            faction.add_subrecord("FULL", b"Faction\0")
            for rank in range(2):
                faction.add_subrecord("RNAM", rank.to_bytes(4, "little"))
                faction.add_subrecord("MNAM", b"Rank\0")
                faction.add_subrecord("FNAM", b"Rank\0")

            for _ in range(2):
                body_part.add_subrecord("BPTN", b"Body part\0")

            faction_group.add_record(faction)
            body_part_group.add_record(body_part)
            writer.add_group(faction_group)
            writer.add_group(body_part_group)
            plugin_path.write_bytes(writer.write_to_bytes())

        plugin_file = PluginFile(name=plugin_path.name, full_path=plugin_path)

        # when
        strings: StringList = plugin_file.get_strings()

        # then
        assert [cast(PluginString, string).type for string in strings] == ["FACT FULL"]

    def test_get_string_contexts(self) -> None:
        """
        Tests that the context of a plugin string contains the other strings of its
        record, independently of the load order index.
        """

        # given
        mod_file_path = Path("Test.esp")
        name = PluginString(
            form_id="05000833|Test.esp", type="WEAP FULL", original="Elite Wolf Bow"
        )
        description = PluginString(
            form_id="0A000833|Test.esp", type="WEAP DESC", original="A sturdy bow."
        )
        other_record = PluginString(
            form_id="05000834|Test.esp", type="WEAP FULL", original="Elite Wolf Sword"
        )
        strings: StringList = [name, description, other_record]

        # when
        contexts: dict[String, ModFileContext] = PluginFile.get_string_contexts(
            mod_file_path, [description], {mod_file_path: strings}
        )

        # then
        context: ModFileContext = contexts[description]
        assert context.string_kind == "Weapon - Description"
        assert [related.string for related in context.related_strings] == [name]
        assert [related.relation for related in context.related_strings] == ["Name"]

    def test_get_string_contexts_limits_siblings(self) -> None:
        """
        Tests that names are preferred over the nearest repeated strings of a record.
        """

        # given
        mod_file_path = Path("Test.esp")
        quest_name = PluginString(
            form_id="05000001|Test.esp", type="QUST FULL", original="Quest"
        )
        entries: list[PluginString] = [
            PluginString(
                form_id="05000001|Test.esp",
                type="QUST CNAM",
                index=index,
                original=f"Entry {index}",
            )
            for index in range(20)
        ]
        strings: StringList = [quest_name, *entries]

        # when
        contexts: dict[String, ModFileContext] = PluginFile.get_string_contexts(
            mod_file_path, [entries[10]], {mod_file_path: strings}
        )

        # then
        related_strings: list[String] = [
            related.string for related in contexts[entries[10]].related_strings
        ]
        assert len(related_strings) == PluginFile.MAX_SIBLINGS
        assert related_strings[0] == quest_name
        assert entries[9] in related_strings
        assert entries[11] in related_strings
        assert entries[0] not in related_strings

    def test_duplicate_strings_are_skipped(self, tmp_path: Path) -> None:
        """
        Tests that a malformed record with two responses of the same number doesn't
        prevent extracting the other strings of the plugin.
        """

        # given
        plugin_path: Path = tmp_path / "Duplicate.esp"
        with (
            PluginWriter(Game.SKYRIM_SE) as writer,
            WritableGroup.new("DIAL") as topic_group,
            WritableRecord.new("DIAL", form_id=0x800) as topic,
            WritableGroup.new(pack("<I", 0x800), group_type=7) as children,
            WritableRecord.new("INFO", form_id=0x801) as info,
        ):
            topic.add_subrecord("EDID", b"Topic\0")
            topic.add_subrecord("FULL", b"Topic text\0")
            topic.add_subrecord("DATA", pack("<BBH", 0, 0, 0))
            topic.add_subrecord("SNAM", b"CUST")
            info.add_subrecord("ENAM", pack("<HH", 0, 0))
            info.add_subrecord(
                "TRDT",
                pack("<II4sB3sIB3s", 0, 50, bytes(4), 1, bytes(3), 0, 0, bytes(3)),
            )
            info.add_subrecord("NAM1", b"First response\0")
            info.add_subrecord("NAM1", b"Second response\0")

            topic_group.add_record(topic)
            children.add_record(info)
            topic_group.add_group(children)
            writer.add_group(topic_group)
            plugin_path.write_bytes(writer.write_to_bytes())

        plugin_file = PluginFile(name=plugin_path.name, full_path=plugin_path)

        # when
        strings: StringList = plugin_file.get_strings()

        # then
        assert [string.original for string in strings] == [
            "Topic text",
            "First response",
        ]
