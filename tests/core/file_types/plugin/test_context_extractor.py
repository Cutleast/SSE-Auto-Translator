"""
Copyright (c) Cutleast
"""

import struct
from pathlib import Path

import pytest
from bethkit import Game, PluginWriter, WritableGroup, WritableRecord
from cutleast_core_lib.core.utilities.reference_dict import ReferenceDict

from core.file_types.plugin.file import PluginFile
from core.file_types.plugin.string import PluginString
from core.mod_file.context import ModFileContext
from core.string.types import String, StringList
from core.translation_context.reference_resolver import ReferenceResolver


class TestPluginContextExtractor:
    """
    Tests `core.file_types.plugin.context_extractor.PluginContextExtractor`.
    """

    PLUGIN_NAME: str = "Dialogue.esp"
    """Name of the test plugin."""

    VANILLA_STRINGS: dict[Path, StringList] = {
        Path("Skyrim.esm"): [
            PluginString(
                form_id="000A2C94|Skyrim.esm",
                type="NPC_ FULL",
                original="Lydia",
                string="Lydia (DE)",
            ),
            PluginString(
                form_id="000139B5|Skyrim.esm",
                type="WEAP FULL",
                original="Daedric Bow",
                string="Daedrischer Bogen",
            ),
        ]
    }
    """Strings of the master of the test plugin."""

    @staticmethod
    def __condition(function: int, parameter: int) -> bytes:
        """
        Creates a condition in the form "function(parameter) == 1".

        Args:
            function (int): Index of the condition function.
            parameter (int): First parameter of the function.

        Returns:
            bytes: Raw condition data.
        """

        return struct.pack(
            "<B3sfHHIIIIi", 0, bytes(3), 1.0, function, 0, parameter, 0, 0, 0, -1
        )

    @staticmethod
    def __response(record: WritableRecord, text: str, emotion: int, notes: str) -> None:
        """
        Adds a single response to a dialogue record.

        Args:
            record (WritableRecord): Dialogue record.
            text (str): Response text.
            emotion (int): Emotion type of the response.
            notes (str): Voice acting notes of the response.
        """

        record.add_subrecord(
            "TRDT",
            struct.pack(
                "<II4sB3sIB3s", emotion, 50, bytes(4), 1, bytes(3), 0, 0, bytes(3)
            ),
        )
        record.add_subrecord("NAM1", text.encode() + b"\0")
        record.add_subrecord("NAM2", notes.encode() + b"\0")
        record.add_subrecord("NAM3", b"\0")

    @pytest.fixture
    def plugin_path(self, tmp_path: Path) -> Path:
        """
        Creates a plugin with dialogue, a quest, an NPC and a weapon.

        Args:
            tmp_path (Path): Temporary folder.

        Returns:
            Path: Path to the plugin.
        """

        path: Path = tmp_path / TestPluginContextExtractor.PLUGIN_NAME
        with (
            PluginWriter(Game.SKYRIM_SE) as writer,
            WritableGroup.new("NPC_") as npc_group,
            WritableRecord.new("NPC_", form_id=0x01000900) as npc,
            WritableGroup.new("WEAP") as weapon_group,
            WritableRecord.new("WEAP", form_id=0x01000A00) as weapon,
            WritableGroup.new("QUST") as quest_group,
            WritableRecord.new("QUST", form_id=0x01000700) as quest,
            WritableGroup.new("DIAL") as topic_group,
            WritableRecord.new("DIAL", form_id=0x01000800) as topic,
            WritableGroup.new(struct.pack("<I", 0x01000800), group_type=7) as children,
            WritableRecord.new("INFO", form_id=0x01000801) as first_info,
            WritableRecord.new("INFO", form_id=0x01000802) as second_info,
            WritableGroup.new("MGEF") as effect_group,
            WritableRecord.new("MGEF", form_id=0x01000B00) as effect,
            WritableGroup.new("SPEL") as spell_group,
            WritableRecord.new("SPEL", form_id=0x01000B01) as spell,
            WritableGroup.new("MESG") as message_group,
            WritableRecord.new("MESG", form_id=0x01000B02) as message,
        ):
            writer.add_master("Skyrim.esm")

            npc.add_subrecord("EDID", b"TestNpc\0")
            npc.add_subrecord("ACBS", struct.pack("<I", 1) + bytes(20))
            npc.add_subrecord("FULL", b"Serana Jr.\0")

            weapon.add_subrecord("EDID", b"TestBow\0")
            weapon.add_subrecord("FULL", b"Elite Wolf Bow\0")
            weapon.add_subrecord("DNAM", bytes([7]) + bytes(99))
            weapon.add_subrecord("CNAM", struct.pack("<I", 0x000139B5))

            quest.add_subrecord("EDID", b"TestQuest\0")
            quest.add_subrecord("FULL", b"The Test Quest\0")
            quest.add_subrecord("DNAM", struct.pack("<HBBIB3s", 0, 0, 0, 0, 8, bytes(3)))
            quest.add_subrecord("INDX", struct.pack("<HBB", 10, 0, 0))
            quest.add_subrecord("QSDT", b"\x01")
            quest.add_subrecord("CNAM", b"I finished the test.\0")

            topic.add_subrecord("EDID", b"TestTopic\0")
            topic.add_subrecord("FULL", b"What do you sell?\0")
            topic.add_subrecord("PNAM", struct.pack("<f", 50.0))
            topic.add_subrecord("QNAM", struct.pack("<I", 0x01000700))
            topic.add_subrecord("DATA", struct.pack("<BBH", 0, 0, 0))
            topic.add_subrecord("SNAM", b"CUST")
            topic.add_subrecord("TIFC", struct.pack("<I", 2))

            first_info.add_subrecord("ENAM", struct.pack("<HH", 0, 0))
            TestPluginContextExtractor.__response(
                first_info, "Only the finest wares.", 1, "(proudly)"
            )
            first_info.add_subrecord(
                "CTDA", TestPluginContextExtractor.__condition(72, 0x000A2C94)
            )
            first_info.add_subrecord(
                "CTDA", TestPluginContextExtractor.__condition(70, 1)
            )

            second_info.add_subrecord("ENAM", struct.pack("<HH", 0, 0))
            TestPluginContextExtractor.__response(second_info, "Come back soon.", 0, "")
            second_info.add_subrecord("ANAM", struct.pack("<I", 0x01000900))

            effect.add_subrecord("EDID", b"TestEffect\0")
            effect.add_subrecord("FULL", b"Frost Damage\0")
            # Flags, base cost, associated item and the skill "Destruction" (20)
            effect.add_subrecord(
                "DATA", struct.pack("<IfIi", 0, 1.0, 0, 20) + bytes(136)
            )

            spell.add_subrecord("EDID", b"TestSpell\0")
            spell.add_subrecord("FULL", b"Frost Breath\0")
            # Base cost, flags and the type "Power" (2) followed by the casting data
            spell.add_subrecord("SPIT", struct.pack("<III", 0, 0, 2) + bytes(24))
            spell.add_subrecord("EFID", struct.pack("<I", 0x01000B00))
            spell.add_subrecord("EFIT", struct.pack("<fII", 10.0, 0, 0))

            message.add_subrecord("EDID", b"TestMessage\0")
            message.add_subrecord("DESC", b"Do you want to rest?\0")
            message.add_subrecord("DNAM", struct.pack("<I", 1))

            effect_group.add_record(effect)
            spell_group.add_record(spell)
            message_group.add_record(message)
            npc_group.add_record(npc)
            weapon_group.add_record(weapon)
            quest_group.add_record(quest)
            topic_group.add_record(topic)
            children.add_record(first_info)
            children.add_record(second_info)
            topic_group.add_group(children)
            for group in [
                npc_group,
                weapon_group,
                quest_group,
                topic_group,
                effect_group,
                spell_group,
                message_group,
            ]:
                writer.add_group(group)

            path.write_bytes(writer.write_to_bytes())

        return path

    @pytest.fixture
    def contexts(self, plugin_path: Path) -> dict[str, ModFileContext]:
        """
        Extracts the contexts of all strings of the test plugin.

        Args:
            plugin_path (Path): Path to the test plugin.

        Returns:
            dict[str, ModFileContext]: The context for each string by its type and text.
        """

        plugin_file = PluginFile(name=plugin_path.name, full_path=plugin_path)
        strings: StringList = plugin_file.get_strings()
        all_strings: dict[Path, StringList] = {Path(plugin_path.name): strings}
        resolver = ReferenceResolver(
            [all_strings, TestPluginContextExtractor.VANILLA_STRINGS]
        )

        contexts: ReferenceDict[String, ModFileContext] = plugin_file.get_contexts(
            strings, all_strings, resolver
        )

        return {
            f"{string.type} {string.original}": context
            for string, context in contexts.items()
            if isinstance(string, PluginString)
        }

    @staticmethod
    def __properties(context: ModFileContext) -> dict[str, str]:
        """
        Gets the properties of a context as a dictionary.

        Args:
            context (ModFileContext): Context to get the properties from.

        Returns:
            dict[str, str]: Property values by their label.
        """

        return {item.label: item.value for item in context.properties}

    def test_dialogue_with_conditions(self, contexts: dict[str, ModFileContext]) -> None:
        """
        Tests resolving the topic, quest and speaker of a dialogue from its conditions.

        Args:
            contexts (dict[str, ModFileContext]): Contexts of the test plugin.
        """

        # when
        context: ModFileContext = contexts["INFO NAM1 Only the finest wares."]

        # then
        assert TestPluginContextExtractor.__properties(context) == {
            "Quest": "The Test Quest",
            "Speaker": "Lydia → Lydia (DE)",
            "Sex": "Female",
            "Emotion": "Anger (50)",
        }
        assert context.notes == ["(proudly)"]
        assert context.related_strings[0].relation == "Topic"
        assert context.related_strings[0].string.original == "What do you sell?"

    def test_dialogue_with_speaker(self, contexts: dict[str, ModFileContext]) -> None:
        """
        Tests reading the sex of a speaker from the plugin.

        Args:
            contexts (dict[str, ModFileContext]): Contexts of the test plugin.
        """

        # when
        context: ModFileContext = contexts["INFO NAM1 Come back soon."]

        # then
        properties: dict[str, str] = TestPluginContextExtractor.__properties(context)
        assert properties["Speaker"] == "Serana Jr."
        assert properties["Sex"] == "Female"
        assert properties["Emotion"] == "Neutral (50)"
        assert context.notes == []

    def test_topic(self, contexts: dict[str, ModFileContext]) -> None:
        """
        Tests listing the responses of a dialogue topic.

        Args:
            contexts (dict[str, ModFileContext]): Contexts of the test plugin.
        """

        # when
        context: ModFileContext = contexts["DIAL FULL What do you sell?"]

        # then
        assert [related.string.original for related in context.related_strings] == [
            "Only the finest wares.",
            "Come back soon.",
        ]

    def test_journal_entry(self, contexts: dict[str, ModFileContext]) -> None:
        """
        Tests reading the quest type and the stage of a journal entry.

        Args:
            contexts (dict[str, ModFileContext]): Contexts of the test plugin.
        """

        # when
        context: ModFileContext = contexts["QUST CNAM I finished the test."]

        # then
        assert TestPluginContextExtractor.__properties(context) == {
            "Quest type": "Side quest",
            "Quest stage": "10",
            "Stage result": "Completes the quest",
        }
        assert [related.string.original for related in context.related_strings] == [
            "The Test Quest"
        ]

    def test_weapon(self, contexts: dict[str, ModFileContext]) -> None:
        """
        Tests reading the weapon type and resolving the template from a master.

        Args:
            contexts (dict[str, ModFileContext]): Contexts of the test plugin.
        """

        # when
        context: ModFileContext = contexts["WEAP FULL Elite Wolf Bow"]

        # then
        assert context.string_kind == "Weapon - Name"
        assert TestPluginContextExtractor.__properties(context) == {
            "Weapon type": "Bow",
            "Template": "Daedric Bow → Daedrischer Bogen",
        }

    def test_spell_and_magic_effect(self, contexts: dict[str, ModFileContext]) -> None:
        """
        Tests reading the type and the effects of a spell and the school of an effect.

        Args:
            contexts (dict[str, ModFileContext]): Contexts of the test plugin.
        """

        # when
        spell_context: ModFileContext = contexts["SPEL FULL Frost Breath"]
        effect_context: ModFileContext = contexts["MGEF FULL Frost Damage"]

        # then
        assert TestPluginContextExtractor.__properties(spell_context) == {
            "Spell type": "Power",
            "Effects": "Frost Damage",
        }
        assert TestPluginContextExtractor.__properties(effect_context) == {
            "School": "Destruction"
        }

    def test_message(self, contexts: dict[str, ModFileContext]) -> None:
        """
        Tests reading whether a message is shown as message box.

        Args:
            contexts (dict[str, ModFileContext]): Contexts of the test plugin.
        """

        # when
        context: ModFileContext = contexts["MESG DESC Do you want to rest?"]

        # then
        assert TestPluginContextExtractor.__properties(context) == {
            "Display": "Message box"
        }

    def test_load_order_independent_form_id(self, plugin_path: Path) -> None:
        """
        Tests that records are found by their record ID, even if the form ID of a
        string contains a load order index instead of the plugin's master index.

        Args:
            plugin_path (Path): Path to the test plugin.
        """

        # given
        plugin_file = PluginFile(name=plugin_path.name, full_path=plugin_path)
        string = PluginString(
            form_id=f"0E000A00|{plugin_path.name}",
            type="WEAP FULL",
            original="Elite Wolf Bow",
        )
        all_strings: dict[Path, StringList] = {Path(plugin_path.name): [string]}

        # when
        contexts: ReferenceDict[String, ModFileContext] = plugin_file.get_contexts(
            [string], all_strings, ReferenceResolver([all_strings])
        )

        # then
        assert TestPluginContextExtractor.__properties(contexts[string]) == {
            "Weapon type": "Bow"
        }
