"""
Copyright (c) Cutleast
"""

import logging
import struct
from typing import ClassVar, Optional

from bethkit import BethkitError, Group, Plugin, Record, SubRecord
from pydantic import BaseModel
from PySide6.QtWidgets import QApplication

from core.mod_file.context import ModFileContext
from core.translation_context.context_property import ContextProperty
from core.translation_context.reference_resolver import (
    ReferenceResolver,
    ResolvedString,
)
from core.translation_context.related_string import RelatedString

from .string import PluginString
from .string_indexes import StringIndexes


class PluginContextExtractor:
    """
    Extracts context for plugin strings from the records of their plugin and from the
    records that they reference.
    """

    class DialogueData(BaseModel, frozen=True):
        """
        Context-relevant data parsed from a dialogue record.
        """

        speaker: Optional[int]
        """Raw form ID of the speaker, if known."""

        female: Optional[bool]
        """Whether the speaker is female according to the conditions, if known."""

        previous_info: Optional[int]
        """Raw form ID of the previous dialogue, if any."""

        emotion: Optional[str]
        """Localized emotion of the requested response, if any."""

        notes: list[str]
        """Voice acting notes of the requested response."""

    SUPPORTED_RECORD_TYPES: ClassVar[list[str]] = [
        "ALCH",
        "AMMO",
        "ARMO",
        "BOOK",
        "CELL",
        "DIAL",
        "ENCH",
        "FLOR",
        "INFO",
        "INGR",
        "LCTN",
        "MESG",
        "MGEF",
        "NPC_",
        "QUST",
        "SCRL",
        "SHOU",
        "SPEL",
        "WEAP",
        "WRLD",
    ]
    """Record types whose strings get context from their records."""

    MAX_EFFECTS: ClassVar[int] = 5
    """Maximum number of magic effects listed for spells, potions and the like."""

    MAX_TOPIC_RESPONSES: ClassVar[int] = 3
    """Maximum number of responses shown as related strings of a dialogue topic."""

    TOPIC_CHILDREN_GROUP_TYPE: ClassVar[int] = 7
    """Group type of the group containing the responses of a dialogue topic."""

    GET_IS_ID_FUNCTION: ClassVar[int] = 72
    """Index of the condition function `GetIsID`."""

    GET_IS_SEX_FUNCTION: ClassVar[int] = 70
    """Index of the condition function `GetIsSex`."""

    __plugin: Plugin
    __resolver: ReferenceResolver
    __plugin_name: str
    __topics: Optional[dict[int, Record]]
    __topic_responses: Optional[dict[int, list[int]]]

    log: logging.Logger = logging.getLogger("PluginContextExtractor")

    def __init__(
        self, plugin: Plugin, resolver: ReferenceResolver, plugin_name: str
    ) -> None:
        """
        Args:
            plugin (Plugin): Open plugin containing the strings.
            resolver (ReferenceResolver): Resolver for referenced records.
            plugin_name (str): File name of the plugin.
        """

        self.__plugin = plugin
        self.__resolver = resolver
        self.__plugin_name = plugin_name
        self.__topics = None
        self.__topic_responses = None

    @staticmethod
    def supports(string: PluginString) -> bool:
        """
        Checks whether context can be extracted for a string.

        Args:
            string (PluginString): String to check.

        Returns:
            bool: Whether context can be extracted for the string.
        """

        return string.type[:4] in PluginContextExtractor.SUPPORTED_RECORD_TYPES

    def extract(self, string: PluginString) -> ModFileContext:
        """
        Extracts the context of a string from its record.

        Args:
            string (PluginString): String to extract the context for.

        Returns:
            ModFileContext:
                The context containing only properties, notes and related strings that
                originate from records.
        """

        form_id: Optional[int] = self.__get_form_id(string)
        record: Optional[Record] = (
            self.__plugin.find_record(form_id) if form_id is not None else None
        )
        if record is None:
            return ModFileContext()

        try:
            match record.signature:
                case b"INFO":
                    return self.__extract_info(string, record)
                case b"DIAL":
                    return self.__extract_topic(record)
                case b"QUST":
                    return self.__extract_quest(string, record)
                case b"BOOK":
                    return self.__extract_book(record)
                case b"WEAP":
                    return self.__extract_weapon(record)
                case b"ARMO":
                    return self.__extract_armor(record)
                case b"NPC_":
                    return self.__extract_npc(record)
                case b"SPEL":
                    return self.__extract_spell(record)
                case b"ALCH":
                    return self.__extract_potion(record)
                case b"ENCH" | b"SCRL" | b"INGR":
                    return ModFileContext(properties=self.__get_effects_property(record))
                case b"MGEF":
                    return PluginContextExtractor.__extract_magic_effect(record)
                case b"MESG":
                    return PluginContextExtractor.__extract_message(record)
                case b"AMMO":
                    return PluginContextExtractor.__extract_ammunition(record)
                case b"SHOU":
                    return self.__extract_shout(record)
                case b"FLOR" | b"LCTN" | b"CELL" | b"WRLD":
                    return self.__extract_reference(record)
                case _:
                    return ModFileContext()

        except (BethkitError, IndexError, struct.error) as ex:
            self.log.warning(
                f"Failed to extract context for '{string.display_id}': {ex}",
                exc_info=ex,
            )
            return ModFileContext()

    def __get_form_id(self, string: PluginString) -> Optional[int]:
        """
        Gets the plugin-local form ID of the record of a string. The form ID is derived
        from the record ID, as the master index of the string's form ID may refer to a
        load order instead of the masters of the plugin.

        Args:
            string (PluginString): String to get the form ID for.

        Returns:
            Optional[int]: The raw form ID or None if its master is unknown.
        """

        object_id, _, master = string.record_id.partition("|")
        masters: list[str] = [master.lower() for master in self.__plugin.masters]

        master_index: int
        if master in masters:
            master_index = masters.index(master)
        elif master == self.__plugin_name.lower():
            master_index = len(masters)
        else:
            return None

        try:
            return master_index << 24 | int(object_id, 16)
        except ValueError:
            return None

    def __extract_info(self, string: PluginString, record: Record) -> ModFileContext:
        """
        Extracts the topic, quest, speaker, emotion and voice acting notes of a dialogue
        response or player prompt.

        Args:
            string (PluginString): String from the record.
            record (Record): Dialogue record.

        Returns:
            ModFileContext: The extracted context.
        """

        dialogue: PluginContextExtractor.DialogueData = (
            PluginContextExtractor.__parse_dialogue(
                record, string.index if string.type == "INFO NAM1" else None
            )
        )
        properties: list[ContextProperty] = []
        related_strings: list[RelatedString] = []

        topic: Optional[Record] = self.__get_topic(record.form_id)
        if topic is not None:
            related_strings += self.__resolve_related(
                topic.form_id,
                "DIAL FULL",
                QApplication.translate("PluginContextExtractor", "Topic"),
            )
            properties += self.__get_quest_property(topic)

        speaker_name: Optional[str] = (
            self.__resolve_name(dialogue.speaker, "NPC_ FULL")
            if dialogue.speaker is not None
            else None
        )
        if speaker_name is not None:
            properties.append(
                ContextProperty(
                    label=QApplication.translate("PluginContextExtractor", "Speaker"),
                    value=speaker_name,
                )
            )

        female: Optional[bool] = dialogue.female
        if female is None and dialogue.speaker is not None:
            female = self.__is_female_npc(dialogue.speaker)

        if female is not None:
            properties.append(PluginContextExtractor.__get_sex_property(female))

        if dialogue.emotion is not None:
            properties.append(
                ContextProperty(
                    label=QApplication.translate("PluginContextExtractor", "Emotion"),
                    value=dialogue.emotion,
                )
            )

        if dialogue.previous_info is not None:
            related_strings += self.__resolve_related(
                dialogue.previous_info,
                "INFO NAM1",
                QApplication.translate("PluginContextExtractor", "Previous dialogue"),
            )

        return ModFileContext(
            properties=properties, notes=dialogue.notes, related_strings=related_strings
        )

    @staticmethod
    def __parse_dialogue(record: Record, response_number: Optional[int]) -> DialogueData:
        """
        Parses the subrecords of a dialogue record. The record is parsed directly as
        decoding it with its schema is too slow for plugins with thousands of
        dialogues.

        Args:
            record (Record): Dialogue record.
            response_number (Optional[int]):
                Number of the response to get the emotion and notes of, if any.

        Returns:
            DialogueData: The parsed data.
        """

        speaker: Optional[int] = None
        condition_speaker: Optional[int] = None
        female: Optional[bool] = None
        previous_info: Optional[int] = None
        emotion: Optional[str] = None
        notes: list[str] = []

        current_response: Optional[int] = None
        for subrecord in record:
            data: bytes = subrecord.raw_bytes
            match subrecord.signature:
                case b"ANAM" if len(data) == 4:
                    speaker = int.from_bytes(data, "little") or None
                case b"PNAM" if len(data) == 4:
                    previous_info = int.from_bytes(data, "little") or None
                case b"TRDT" if len(data) >= 13:
                    current_response = data[12]
                    if current_response == response_number:
                        emotion = (
                            PluginContextExtractor.__get_emotion_name(
                                int.from_bytes(data[0:4], "little")
                            )
                            + f" ({int.from_bytes(data[4:8], 'little')})"
                        )
                case b"NAM2" | b"NAM3" if current_response == response_number:
                    note: str = PluginContextExtractor.__decode_text(data).strip()
                    if note:
                        notes.append(note)
                case b"CTDA":
                    condition: Optional[tuple[int, int]] = (
                        PluginContextExtractor.__parse_true_condition(data)
                    )
                    if condition is None:
                        continue

                    function, parameter = condition
                    if function == PluginContextExtractor.GET_IS_ID_FUNCTION:
                        condition_speaker = condition_speaker or parameter or None
                    elif function == PluginContextExtractor.GET_IS_SEX_FUNCTION:
                        female = parameter == 1

        return PluginContextExtractor.DialogueData(
            speaker=speaker or condition_speaker,
            female=female,
            previous_info=previous_info,
            emotion=emotion,
            notes=notes,
        )

    @staticmethod
    def __parse_true_condition(data: bytes) -> Optional[tuple[int, int]]:
        """
        Parses a condition in the form "function(parameter) == 1".

        Args:
            data (bytes): Raw condition data.

        Returns:
            Optional[tuple[int, int]]:
                The function index and its first parameter or None if the condition
                has another form.
        """

        if len(data) < 16:
            return None

        condition_type: int = data[0]
        # The upper three bits contain the operator, where 0 is "equal to", and the
        # third bit marks a global variable as comparison value.
        if condition_type >> 5 != 0 or condition_type & 4:
            return None

        comparison_value: float = struct.unpack("<f", data[4:8])[0]
        if comparison_value != 1.0:
            return None

        return (
            int.from_bytes(data[8:10], "little"),
            int.from_bytes(data[12:16], "little"),
        )

    @staticmethod
    def __decode_text(data: bytes) -> str:
        """
        Decodes a null-terminated text that is not translatable and therefore not
        handled by the plugin's string encoding.

        Args:
            data (bytes): Raw text data.

        Returns:
            str: The decoded text.
        """

        text: bytes = data.split(b"\0", 1)[0]
        try:
            return text.decode("utf-8")
        except UnicodeDecodeError:
            return text.decode("cp1252", errors="replace")

    def __is_female_npc(self, npc_form_id: int) -> Optional[bool]:
        """
        Checks whether an NPC is female. Only works for NPCs from the current plugin.

        Args:
            npc_form_id (int): Raw form ID of the NPC.

        Returns:
            Optional[bool]: Whether the NPC is female, if known.
        """

        if npc_form_id >> 24 != len(self.__plugin.masters):
            return None

        npc: Optional[Record] = self.__plugin.find_record(npc_form_id)
        if npc is None or npc.signature != b"NPC_":
            return None

        configuration: Optional[SubRecord] = npc.find_subrecord("ACBS")
        if configuration is None:
            return None

        # The first bit of the flags at the start of the configuration marks females.
        return bool(configuration.raw_bytes[0] & 1)

    def __extract_topic(self, record: Record) -> ModFileContext:
        """
        Extracts the quest and the first responses of a dialogue topic.

        Args:
            record (Record): Dialogue topic record.

        Returns:
            ModFileContext: The extracted context.
        """

        related_strings: list[RelatedString] = []
        for response in self.__get_topic_responses(record.form_id)[
            : PluginContextExtractor.MAX_TOPIC_RESPONSES
        ]:
            related_strings += self.__resolve_related(
                response,
                "INFO NAM1",
                QApplication.translate("PluginContextExtractor", "Response"),
            )

        return ModFileContext(
            properties=self.__get_quest_property(record),
            related_strings=related_strings,
        )

    def __get_quest_property(self, topic: Record) -> list[ContextProperty]:
        """
        Gets the quest of a dialogue topic.

        Args:
            topic (Record): Dialogue topic record.

        Returns:
            list[ContextProperty]: The quest property if the topic has a named quest.
        """

        quest: Optional[SubRecord] = topic.find_subrecord("QNAM")
        if quest is None or not quest.as_u32():
            return []

        quest_name: Optional[str] = self.__resolve_name(quest.as_u32(), "QUST FULL")
        if quest_name is None:
            return []

        return [
            ContextProperty(
                label=QApplication.translate("PluginContextExtractor", "Quest"),
                value=quest_name,
            )
        ]

    def __extract_quest(self, string: PluginString, record: Record) -> ModFileContext:
        """
        Extracts the quest type and, for journal entries, the quest stage.

        Args:
            string (PluginString): String from the record.
            record (Record): Quest record.

        Returns:
            ModFileContext: The extracted context.
        """

        properties: list[ContextProperty] = []

        quest_data: Optional[SubRecord] = record.find_subrecord("DNAM")
        if quest_data is not None and len(quest_data.raw_bytes) >= 12:
            quest_type: Optional[str] = PluginContextExtractor.__get_quest_type_name(
                quest_data.raw_bytes[8]
            )
            if quest_type is not None:
                properties.append(
                    ContextProperty(
                        label=QApplication.translate(
                            "PluginContextExtractor", "Quest type"
                        ),
                        value=quest_type,
                    )
                )

        subrecord_index: Optional[int] = (
            PluginContextExtractor.__find_journal_entry(record, string.index)
            if string.type == "QUST CNAM"
            else None
        )
        if subrecord_index is not None:
            properties += PluginContextExtractor.__get_stage_properties(
                record, subrecord_index
            )

        return ModFileContext(properties=properties)

    @staticmethod
    def __find_journal_entry(record: Record, index: Optional[int]) -> Optional[int]:
        """
        Finds the subrecord of a journal entry by its string index.

        Args:
            record (Record): Quest record.
            index (Optional[int]): String index of the journal entry.

        Returns:
            Optional[int]: The position of the journal entry subrecord, if found.
        """

        indexes = StringIndexes()
        for position, subrecord in enumerate(record):
            if subrecord.signature == b"CNAM" and indexes.get(record, position) == index:
                return position

        return None

    @staticmethod
    def __get_stage_properties(
        record: Record, subrecord_index: int
    ) -> list[ContextProperty]:
        """
        Gets the stage of a journal entry and whether it completes or fails its quest.

        Args:
            record (Record): Quest record.
            subrecord_index (int): Index of the journal entry subrecord.

        Returns:
            list[ContextProperty]: The stage properties.
        """

        stage: Optional[int] = None
        log_entry_flags: int = 0
        for index, subrecord in enumerate(record):
            if index >= subrecord_index:
                break

            match subrecord.signature:
                case b"INDX":
                    stage = int.from_bytes(subrecord.raw_bytes[:2], "little")
                    log_entry_flags = 0
                case b"QSDT":
                    log_entry_flags = subrecord.raw_bytes[0]

        if stage is None:
            return []

        properties: list[ContextProperty] = [
            ContextProperty(
                label=QApplication.translate("PluginContextExtractor", "Quest stage"),
                value=str(stage),
            )
        ]

        result: Optional[str] = None
        if log_entry_flags & 1:
            result = QApplication.translate(
                "PluginContextExtractor", "Completes the quest"
            )
        elif log_entry_flags & 2:
            result = QApplication.translate("PluginContextExtractor", "Fails the quest")

        if result is not None:
            properties.append(
                ContextProperty(
                    label=QApplication.translate(
                        "PluginContextExtractor", "Stage result"
                    ),
                    value=result,
                )
            )

        return properties

    def __extract_book(self, record: Record) -> ModFileContext:
        """
        Extracts the type of a book and the spell that it teaches.

        Args:
            record (Record): Book record.

        Returns:
            ModFileContext: The extracted context.
        """

        data: Optional[SubRecord] = record.find_subrecord("DATA")
        if data is None or len(data.raw_bytes) < 8:
            return ModFileContext()

        flags: int = data.raw_bytes[0]
        book_type: int = data.raw_bytes[1]
        properties: list[ContextProperty] = [
            ContextProperty(
                label=QApplication.translate("PluginContextExtractor", "Book type"),
                value=(
                    QApplication.translate("PluginContextExtractor", "Note or scroll")
                    if book_type == 0xFF
                    else QApplication.translate("PluginContextExtractor", "Book")
                ),
            )
        ]

        taught: Optional[str] = None
        if flags & 4:
            taught = self.__resolve_name(
                int.from_bytes(data.raw_bytes[4:8], "little"), "SPEL FULL"
            )
        elif flags & 1:
            taught = QApplication.translate("PluginContextExtractor", "A skill")

        if taught is not None:
            properties.append(
                ContextProperty(
                    label=QApplication.translate("PluginContextExtractor", "Teaches"),
                    value=taught,
                )
            )

        return ModFileContext(properties=properties)

    def __extract_weapon(self, record: Record) -> ModFileContext:
        """
        Extracts the type, template and enchantment of a weapon.

        Args:
            record (Record): Weapon record.

        Returns:
            ModFileContext: The extracted context.
        """

        properties: list[ContextProperty] = []

        game_data: Optional[SubRecord] = record.find_subrecord("DNAM")
        if game_data is not None and game_data.raw_bytes:
            weapon_type: Optional[str] = PluginContextExtractor.__get_weapon_type_name(
                game_data.raw_bytes[0]
            )
            if weapon_type is not None:
                properties.append(
                    ContextProperty(
                        label=QApplication.translate(
                            "PluginContextExtractor", "Weapon type"
                        ),
                        value=weapon_type,
                    )
                )

        properties += self.__get_reference_properties(
            record,
            [
                (
                    "CNAM",
                    ["WEAP FULL"],
                    QApplication.translate("PluginContextExtractor", "Template"),
                ),
                (
                    "EITM",
                    ["ENCH FULL", "SCRL FULL"],
                    QApplication.translate("PluginContextExtractor", "Enchantment"),
                ),
            ],
        )

        return ModFileContext(properties=properties)

    def __extract_armor(self, record: Record) -> ModFileContext:
        """
        Extracts the type, template and enchantment of an armor.

        Args:
            record (Record): Armor record.

        Returns:
            ModFileContext: The extracted context.
        """

        properties: list[ContextProperty] = []

        armor_type: Optional[int] = None
        body_template: Optional[SubRecord] = record.find_subrecord("BOD2")
        legacy_body_template: Optional[SubRecord] = record.find_subrecord("BODT")
        if body_template is not None and len(body_template.raw_bytes) >= 8:
            armor_type = int.from_bytes(body_template.raw_bytes[4:8], "little")
        elif (
            legacy_body_template is not None
            and len(legacy_body_template.raw_bytes) >= 12
        ):
            armor_type = int.from_bytes(legacy_body_template.raw_bytes[8:12], "little")

        armor_type_name: Optional[str] = (
            PluginContextExtractor.__get_armor_type_name(armor_type)
            if armor_type is not None
            else None
        )
        if armor_type_name is not None:
            properties.append(
                ContextProperty(
                    label=QApplication.translate("PluginContextExtractor", "Armor type"),
                    value=armor_type_name,
                )
            )

        properties += self.__get_reference_properties(
            record,
            [
                (
                    "TNAM",
                    ["ARMO FULL"],
                    QApplication.translate("PluginContextExtractor", "Template"),
                ),
                (
                    "EITM",
                    ["ENCH FULL"],
                    QApplication.translate("PluginContextExtractor", "Enchantment"),
                ),
            ],
        )

        return ModFileContext(properties=properties)

    def __extract_npc(self, record: Record) -> ModFileContext:
        """
        Extracts the sex, race and class of an NPC.

        Args:
            record (Record): NPC record.

        Returns:
            ModFileContext: The extracted context.
        """

        properties: list[ContextProperty] = []

        female: Optional[bool] = self.__is_female_npc(record.form_id)
        if female is not None:
            properties.append(PluginContextExtractor.__get_sex_property(female))

        properties += self.__get_reference_properties(
            record,
            [
                (
                    "RNAM",
                    ["RACE FULL"],
                    QApplication.translate("PluginContextExtractor", "Race"),
                ),
                (
                    "CNAM",
                    ["CLAS FULL"],
                    QApplication.translate("PluginContextExtractor", "Class"),
                ),
            ],
        )

        return ModFileContext(properties=properties)

    def __extract_spell(self, record: Record) -> ModFileContext:
        """
        Extracts the type and the effects of a spell.

        Args:
            record (Record): Spell record.

        Returns:
            ModFileContext: The extracted context.
        """

        properties: list[ContextProperty] = []

        spell_data: Optional[SubRecord] = record.find_subrecord("SPIT")
        if spell_data is not None and len(spell_data.raw_bytes) >= 12:
            spell_type: Optional[str] = PluginContextExtractor.__get_spell_type_name(
                int.from_bytes(spell_data.raw_bytes[8:12], "little")
            )
            if spell_type is not None:
                properties.append(
                    ContextProperty(
                        label=QApplication.translate(
                            "PluginContextExtractor", "Spell type"
                        ),
                        value=spell_type,
                    )
                )

        properties += self.__get_effects_property(record)

        return ModFileContext(properties=properties)

    def __extract_potion(self, record: Record) -> ModFileContext:
        """
        Extracts whether a potion is food or poison and its effects.

        Args:
            record (Record): Potion record.

        Returns:
            ModFileContext: The extracted context.
        """

        properties: list[ContextProperty] = []

        potion_data: Optional[SubRecord] = record.find_subrecord("ENIT")
        if potion_data is not None and len(potion_data.raw_bytes) >= 8:
            flags: int = int.from_bytes(potion_data.raw_bytes[4:8], "little")
            potion_type: str
            if flags & 0x20000:
                potion_type = QApplication.translate("PluginContextExtractor", "Poison")
            elif flags & 0x2:
                potion_type = QApplication.translate("PluginContextExtractor", "Food")
            else:
                potion_type = QApplication.translate("PluginContextExtractor", "Potion")

            properties.append(
                ContextProperty(
                    label=QApplication.translate("PluginContextExtractor", "Type"),
                    value=potion_type,
                )
            )

        properties += self.__get_effects_property(record)

        return ModFileContext(properties=properties)

    def __get_effects_property(self, record: Record) -> list[ContextProperty]:
        """
        Gets the names of the magic effects of a spell, enchantment, potion and the like.

        Args:
            record (Record): Record with magic effects.

        Returns:
            list[ContextProperty]: The effects property if any effect has a name.
        """

        effect_names: list[str] = []
        for subrecord in record:
            if subrecord.signature != b"EFID" or len(subrecord.raw_bytes) != 4:
                continue

            effect_name: Optional[str] = self.__resolve_name(
                subrecord.as_u32(), "MGEF FULL"
            )
            if effect_name is not None and effect_name not in effect_names:
                effect_names.append(effect_name)

        if not effect_names:
            return []

        if len(effect_names) > PluginContextExtractor.MAX_EFFECTS:
            effect_names = effect_names[: PluginContextExtractor.MAX_EFFECTS] + ["..."]

        return [
            ContextProperty(
                label=QApplication.translate("PluginContextExtractor", "Effects"),
                value=", ".join(effect_names),
            )
        ]

    @staticmethod
    def __extract_magic_effect(record: Record) -> ModFileContext:
        """
        Extracts the magic school of a magic effect.

        Args:
            record (Record): Magic effect record.

        Returns:
            ModFileContext: The extracted context.
        """

        effect_data: Optional[SubRecord] = record.find_subrecord("DATA")
        if effect_data is None or len(effect_data.raw_bytes) < 16:
            return ModFileContext()

        school: Optional[str] = PluginContextExtractor.__get_school_name(
            int.from_bytes(effect_data.raw_bytes[12:16], "little", signed=True)
        )
        if school is None:
            return ModFileContext()

        return ModFileContext(
            properties=[
                ContextProperty(
                    label=QApplication.translate("PluginContextExtractor", "School"),
                    value=school,
                )
            ]
        )

    @staticmethod
    def __extract_message(record: Record) -> ModFileContext:
        """
        Extracts whether a message is shown as message box or as notification.

        Args:
            record (Record): Message record.

        Returns:
            ModFileContext: The extracted context.
        """

        flags: Optional[SubRecord] = record.find_subrecord("DNAM")
        if flags is None or not flags.raw_bytes:
            return ModFileContext()

        return ModFileContext(
            properties=[
                ContextProperty(
                    label=QApplication.translate("PluginContextExtractor", "Display"),
                    value=(
                        QApplication.translate("PluginContextExtractor", "Message box")
                        if flags.raw_bytes[0] & 1
                        else QApplication.translate(
                            "PluginContextExtractor", "Notification"
                        )
                    ),
                )
            ]
        )

    @staticmethod
    def __extract_ammunition(record: Record) -> ModFileContext:
        """
        Extracts whether an ammunition is an arrow or a bolt.

        Args:
            record (Record): Ammunition record.

        Returns:
            ModFileContext: The extracted context.
        """

        ammunition_data: Optional[SubRecord] = record.find_subrecord("DATA")
        if ammunition_data is None or len(ammunition_data.raw_bytes) < 8:
            return ModFileContext()

        flags: int = int.from_bytes(ammunition_data.raw_bytes[4:8], "little")

        return ModFileContext(
            properties=[
                ContextProperty(
                    label=QApplication.translate(
                        "PluginContextExtractor", "Ammunition type"
                    ),
                    value=(
                        QApplication.translate("PluginContextExtractor", "Arrow")
                        if flags & 4
                        else QApplication.translate("PluginContextExtractor", "Bolt")
                    ),
                )
            ]
        )

    def __extract_shout(self, record: Record) -> ModFileContext:
        """
        Extracts the words of power of a shout.

        Args:
            record (Record): Shout record.

        Returns:
            ModFileContext: The extracted context.
        """

        words: list[str] = []
        for subrecord in record:
            if subrecord.signature != b"SNAM" or len(subrecord.raw_bytes) < 4:
                continue

            word: Optional[str] = self.__resolve_name(
                int.from_bytes(subrecord.raw_bytes[:4], "little"), "WOOP FULL"
            )
            if word is not None:
                words.append(word)

        if not words:
            return ModFileContext()

        return ModFileContext(
            properties=[
                ContextProperty(
                    label=QApplication.translate(
                        "PluginContextExtractor", "Words of power"
                    ),
                    value=", ".join(words),
                )
            ]
        )

    def __extract_reference(self, record: Record) -> ModFileContext:
        """
        Extracts the name of the record that a flora, location, cell or worldspace
        refers to, like the ingredient of a flora or the parent of a location.

        Args:
            record (Record): Flora, location, cell or worldspace record.

        Returns:
            ModFileContext: The extracted context.
        """

        references: dict[bytes, tuple[str, list[str], str]] = {
            b"FLOR": (
                "PFIG",
                ["INGR FULL", "ALCH FULL", "MISC FULL"],
                QApplication.translate("PluginContextExtractor", "Ingredient"),
            ),
            b"LCTN": (
                "PNAM",
                ["LCTN FULL"],
                QApplication.translate("PluginContextExtractor", "Parent location"),
            ),
            b"CELL": (
                "XLCN",
                ["LCTN FULL"],
                QApplication.translate("PluginContextExtractor", "Location"),
            ),
            b"WRLD": (
                "WNAM",
                ["WRLD FULL"],
                QApplication.translate("PluginContextExtractor", "Parent worldspace"),
            ),
        }

        reference: Optional[tuple[str, list[str], str]] = references.get(
            record.signature
        )
        if reference is None:
            return ModFileContext()

        return ModFileContext(
            properties=self.__get_reference_properties(record, [reference])
        )

    def __get_reference_properties(
        self, record: Record, references: list[tuple[str, list[str], str]]
    ) -> list[ContextProperty]:
        """
        Gets the names of records referenced by form ID subrecords.

        Args:
            record (Record): Record containing the references.
            references (list[tuple[str, list[str], str]]):
                Signature of the subrecord containing the form ID, possible string
                types of the name of the referenced record and localized label of the
                property.

        Returns:
            list[ContextProperty]: Properties for all references with a known name.
        """

        properties: list[ContextProperty] = []
        for signature, string_types, label in references:
            subrecord: Optional[SubRecord] = record.find_subrecord(signature)
            if subrecord is None or len(subrecord.raw_bytes) != 4:
                continue

            name: Optional[str] = next(
                (
                    name
                    for string_type in string_types
                    if (name := self.__resolve_name(subrecord.as_u32(), string_type))
                    is not None
                ),
                None,
            )
            if name is not None:
                properties.append(ContextProperty(label=label, value=name))

        return properties

    def __get_topic(self, info_form_id: int) -> Optional[Record]:
        """
        Gets the dialogue topic of a dialogue response.

        Args:
            info_form_id (int): Raw form ID of the dialogue response.

        Returns:
            Optional[Record]: The dialogue topic if it is in the current plugin.
        """

        if self.__topics is None:
            self.__index_topics()

        assert self.__topics is not None
        return self.__topics.get(info_form_id)

    def __get_topic_responses(self, topic_form_id: int) -> list[int]:
        """
        Gets the dialogue responses of a dialogue topic.

        Args:
            topic_form_id (int): Raw form ID of the dialogue topic.

        Returns:
            list[int]: The raw form IDs of the responses.
        """

        if self.__topic_responses is None:
            self.__index_topics()

        assert self.__topic_responses is not None
        return self.__topic_responses.get(topic_form_id, [])

    def __index_topics(self) -> None:
        """
        Indexes the relation between dialogue topics and their responses. Responses are
        not linked to their topic by a field but stored in a group directly following
        the topic.
        """

        self.__topics = {}
        self.__topic_responses = {}

        for group in self.__plugin:
            first_record: Optional[Record] = (
                group.child_as_record(0)
                if group.child_count and group.child_is_record(0)
                else None
            )
            if first_record is None or first_record.signature != b"DIAL":
                continue

            topic: Optional[Record] = None
            for child in group:
                if isinstance(child, Record):
                    topic = child
                elif (
                    topic is not None
                    and child.group_type
                    == PluginContextExtractor.TOPIC_CHILDREN_GROUP_TYPE
                ):
                    self.__index_topic_children(topic, child)

    def __index_topic_children(self, topic: Record, children: Group) -> None:
        """
        Indexes the responses of a single dialogue topic.

        Args:
            topic (Record): Dialogue topic record.
            children (Group): Group containing the responses of the topic.
        """

        assert self.__topics is not None
        assert self.__topic_responses is not None

        responses: list[int] = self.__topic_responses.setdefault(topic.form_id, [])
        for child in children:
            if isinstance(child, Record) and child.signature == b"INFO":
                self.__topics[child.form_id] = topic
                responses.append(child.form_id)

    def __resolve_related(
        self, form_id: int, string_type: str, relation: str
    ) -> list[RelatedString]:
        """
        Resolves the strings of a referenced record as related strings.

        Args:
            form_id (int): Raw form ID of the referenced record.
            string_type (str): Type of the strings to resolve.
            relation (str): Localized relation of the strings.

        Returns:
            list[RelatedString]: The resolved strings.
        """

        return [
            RelatedString(relation=relation, string=string, mod_file=mod_file)
            for string, mod_file in self.__resolve(form_id, string_type)
        ]

    def __resolve_name(self, form_id: int, string_type: str) -> Optional[str]:
        """
        Resolves the name of a referenced record for display.

        Args:
            form_id (int): Raw form ID of the referenced record.
            string_type (str): Type of the name string, for eg. "NPC_ FULL".

        Returns:
            Optional[str]:
                The original name followed by its translation if it was translated.
        """

        resolved_strings: list[ResolvedString] = self.__resolve(form_id, string_type)
        if not resolved_strings:
            return None

        name: PluginString = resolved_strings[0][0]
        if name.string is None or name.string == name.original:
            return name.original

        return f"{name.original} → {name.string}"

    def __resolve(self, form_id: int, string_type: str) -> list[ResolvedString]:
        """
        Resolves the strings of a referenced record.

        Args:
            form_id (int): Raw form ID of the referenced record.
            string_type (str): Type of the strings to resolve.

        Returns:
            list[ResolvedString]: The resolved strings.
        """

        if not form_id:
            return []

        return self.__resolver.resolve(
            ReferenceResolver.get_record_id(
                form_id, self.__plugin_name, self.__plugin.masters
            ),
            string_type,
        )

    @staticmethod
    def __get_sex_property(female: bool) -> ContextProperty:
        """
        Creates the property describing the sex of a character.

        Args:
            female (bool): Whether the character is female.

        Returns:
            ContextProperty: The property.
        """

        return ContextProperty(
            label=QApplication.translate("PluginContextExtractor", "Sex"),
            value=(
                QApplication.translate("PluginContextExtractor", "Female")
                if female
                else QApplication.translate("PluginContextExtractor", "Male")
            ),
        )

    @staticmethod
    def __get_emotion_name(emotion_type: int) -> str:
        """
        Gets the localized name of a dialogue emotion.

        Args:
            emotion_type (int): Emotion type of a dialogue response.

        Returns:
            str: The localized name or the raw value if it is unknown.
        """

        names: list[str] = [
            QApplication.translate("PluginContextExtractor", "Neutral"),
            QApplication.translate("PluginContextExtractor", "Anger"),
            QApplication.translate("PluginContextExtractor", "Disgust"),
            QApplication.translate("PluginContextExtractor", "Fear"),
            QApplication.translate("PluginContextExtractor", "Sad"),
            QApplication.translate("PluginContextExtractor", "Happy"),
            QApplication.translate("PluginContextExtractor", "Surprise"),
            QApplication.translate("PluginContextExtractor", "Puzzled"),
        ]

        return names[emotion_type] if emotion_type < len(names) else str(emotion_type)

    @staticmethod
    def __get_quest_type_name(quest_type: int) -> Optional[str]:
        """
        Gets the localized name of a quest type.

        Args:
            quest_type (int): Quest type of a quest.

        Returns:
            Optional[str]: The localized name or None for unknown quest types.
        """

        names: dict[int, str] = {
            1: QApplication.translate("PluginContextExtractor", "Main quest"),
            2: QApplication.translate("PluginContextExtractor", "Mages Guild"),
            3: QApplication.translate("PluginContextExtractor", "Thieves Guild"),
            4: QApplication.translate("PluginContextExtractor", "Dark Brotherhood"),
            5: QApplication.translate("PluginContextExtractor", "Companions"),
            6: QApplication.translate("PluginContextExtractor", "Miscellaneous"),
            7: QApplication.translate("PluginContextExtractor", "Daedric"),
            8: QApplication.translate("PluginContextExtractor", "Side quest"),
            9: QApplication.translate("PluginContextExtractor", "Civil War"),
            10: QApplication.translate("PluginContextExtractor", "Dawnguard"),
            11: QApplication.translate("PluginContextExtractor", "Dragonborn"),
        }

        return names.get(quest_type)

    @staticmethod
    def __get_weapon_type_name(animation_type: int) -> Optional[str]:
        """
        Gets the localized name of a weapon type.

        Args:
            animation_type (int): Animation type of a weapon.

        Returns:
            Optional[str]: The localized name or None for unknown weapon types.
        """

        names: list[str] = [
            QApplication.translate("PluginContextExtractor", "Hand to hand"),
            QApplication.translate("PluginContextExtractor", "Sword"),
            QApplication.translate("PluginContextExtractor", "Dagger"),
            QApplication.translate("PluginContextExtractor", "War axe"),
            QApplication.translate("PluginContextExtractor", "Mace"),
            QApplication.translate("PluginContextExtractor", "Greatsword"),
            QApplication.translate("PluginContextExtractor", "Battleaxe or warhammer"),
            QApplication.translate("PluginContextExtractor", "Bow"),
            QApplication.translate("PluginContextExtractor", "Staff"),
            QApplication.translate("PluginContextExtractor", "Crossbow"),
        ]

        return names[animation_type] if animation_type < len(names) else None

    @staticmethod
    def __get_armor_type_name(armor_type: int) -> Optional[str]:
        """
        Gets the localized name of an armor type.

        Args:
            armor_type (int): Armor type of an armor.

        Returns:
            Optional[str]: The localized name or None for unknown armor types.
        """

        names: list[str] = [
            QApplication.translate("PluginContextExtractor", "Light armor"),
            QApplication.translate("PluginContextExtractor", "Heavy armor"),
            QApplication.translate("PluginContextExtractor", "Clothing"),
        ]

        return names[armor_type] if armor_type < len(names) else None

    @staticmethod
    def __get_spell_type_name(spell_type: int) -> Optional[str]:
        """
        Gets the localized name of a spell type.

        Args:
            spell_type (int): Type of a spell.

        Returns:
            Optional[str]: The localized name or None for unknown spell types.
        """

        names: dict[int, str] = {
            0: QApplication.translate("PluginContextExtractor", "Spell"),
            1: QApplication.translate("PluginContextExtractor", "Disease"),
            2: QApplication.translate("PluginContextExtractor", "Power"),
            3: QApplication.translate("PluginContextExtractor", "Lesser power"),
            4: QApplication.translate("PluginContextExtractor", "Ability"),
            5: QApplication.translate("PluginContextExtractor", "Poison"),
            10: QApplication.translate("PluginContextExtractor", "Addiction"),
            11: QApplication.translate("PluginContextExtractor", "Shout"),
        }

        return names.get(spell_type)

    @staticmethod
    def __get_school_name(skill: int) -> Optional[str]:
        """
        Gets the localized name of a magic school.

        Args:
            skill (int): Actor value index of the skill of a magic effect.

        Returns:
            Optional[str]: The localized name or None if the skill is no magic school.
        """

        names: dict[int, str] = {
            18: QApplication.translate("PluginContextExtractor", "Alteration"),
            19: QApplication.translate("PluginContextExtractor", "Conjuration"),
            20: QApplication.translate("PluginContextExtractor", "Destruction"),
            21: QApplication.translate("PluginContextExtractor", "Illusion"),
            22: QApplication.translate("PluginContextExtractor", "Restoration"),
        }

        return names.get(skill)
