"""
Copyright (c) Cutleast
"""

import re
from pathlib import Path
from typing import Any, BinaryIO, TypeAlias, override

from pydantic import TypeAdapter, ValidationError

from core.file_source.file_source import FileSource
from core.mod_file.mod_file import ModFile
from core.string.string_status import StringStatus
from core.string.types import StringList

from .string import BestiaryString

LootData: TypeAlias = dict[str, list[tuple[str, str]]]
"""Type alias for the content of a bestiary loot file."""

LootDataAdapter = TypeAdapter(LootData)
"""Type adapter for the content of a bestiary loot file."""

EntryData: TypeAlias = dict[str, Any]
"""Type alias for the content of a bestiary creature file."""

EntryDataAdapter = TypeAdapter(EntryData)
"""Type adapter for the content of a bestiary creature file."""


class BestiaryFile(ModFile):
    """
    Class for Dragonborn's Bestiary files (data/interface/creatures/**/*.json).
    """

    LOOT_KEY: str = "loot"
    """Name of the key attribute in a bestiary loot file."""

    ID_KEY: str = "id"
    """Name of the id attribute in a bestiary creature file."""

    NAME_KEY: str = "name"
    """Name of the name attribute in a bestiary creature file."""

    DESCRIPTION_KEY: str = "description"
    """Name of the description attribute in a bestiary creature file."""

    LOOT_FILE_NAME_PATTERN: re.Pattern[str] = re.compile(
        r"[a-z \-_]+_LOOT *\.json", re.IGNORECASE
    )
    """Pattern for the file name of bestiary loot files."""

    RESIST_FILE_NAME_PATTERN: re.Pattern[str] = re.compile(
        r"[a-z \-_]+_RESIST *\.json", re.IGNORECASE
    )
    """Pattern for the file name of bestiary resistance files."""

    ENTRY_NAME_SUFFIX: str = "-name"
    """ID suffix for identifying the name string of an entry file."""

    ENTRY_DESC_SUFFIX: str = "-description"
    """ID suffix for identifying the description string of an entry file."""

    LOOT_ID_SEP: str = "_LOOT"
    """ID separator for identifying the category of a loot item."""

    @override
    @classmethod
    def get_glob_patterns(cls, language: str) -> list[str]:
        return ["interface/creatures/*/**/*.json"]

    @override
    @classmethod
    def can_be_in_bsas(cls) -> bool:
        return False

    @override
    def _extract_strings(self) -> StringList:
        result: StringList

        file_source: FileSource = FileSource.from_file(self.full_path)
        with file_source.get_file_stream() as stream:
            if BestiaryFile.LOOT_FILE_NAME_PATTERN.match(self.name):
                result = BestiaryFile.extract_strings_from_loot_file(
                    self.full_path.parent.name, stream
                )
            elif BestiaryFile.RESIST_FILE_NAME_PATTERN.match(self.name):
                return []  # resistance files don't contain any translatable strings
            else:
                result = BestiaryFile.extract_strings_from_creature_file(stream)

        return result

    @staticmethod
    def extract_strings_from_creature_file(stream: BinaryIO) -> StringList:
        """
        Extracts strings from the main file belonging to a creature entry in the
        bestiary.

        Args:
            stream (BinaryIO): Binary stream with the contents of the JSON file.

        Returns:
            StringList: List of extracted strings.
        """

        try:
            data: EntryData = EntryDataAdapter.validate_json(stream.read())
        except ValidationError:
            return []

        if any(
            key not in data
            for key in [
                BestiaryFile.ID_KEY,
                BestiaryFile.NAME_KEY,
                BestiaryFile.DESCRIPTION_KEY,
            ]
        ):
            return []

        strings: StringList = []
        creature_id: Any = data[BestiaryFile.ID_KEY]
        assert isinstance(creature_id, str)

        # name of the creature
        name_value: Any = data[BestiaryFile.NAME_KEY]
        assert isinstance(name_value, str)

        strings.append(
            BestiaryString(
                original=name_value,
                status=StringStatus.TranslationRequired,
                bestiary_id=creature_id + BestiaryFile.ENTRY_NAME_SUFFIX,
            )
        )

        # description of the creature
        desc_value: Any = data[BestiaryFile.DESCRIPTION_KEY]
        assert isinstance(desc_value, str)

        strings.append(
            BestiaryString(
                original=desc_value,
                status=StringStatus.TranslationRequired,
                bestiary_id=creature_id + BestiaryFile.ENTRY_DESC_SUFFIX,
            )
        )

        return strings

    @staticmethod
    def extract_strings_from_loot_file(
        creature_id: str, stream: BinaryIO
    ) -> StringList:
        """
        Extracts strings from a loot file belonging to a creature entry in the bestiary.

        Args:
            creature_id (str): ID of the current creature entry.
            stream (BinaryIO): Binary stream with the contents of the JSON file.

        Returns:
            StringList: List of extracted strings.
        """

        try:
            data: LootData = LootDataAdapter.validate_json(stream.read())
        except ValidationError:
            return []

        items: list[tuple[str, str]] = data.get(BestiaryFile.LOOT_KEY, [])

        strings: StringList = []
        for i, item in enumerate(items):
            text: str
            category: str
            text, category = item

            strings.append(
                BestiaryString(
                    original=text,
                    status=StringStatus.TranslationRequired,
                    bestiary_id=(
                        creature_id
                        + BestiaryFile.LOOT_ID_SEP
                        + f"-{i}/{len(items)}-"
                        + category
                    ),
                )
            )

        return strings

    @override
    def dump_strings(
        self,
        strings: StringList,
        output_folder: Path,
        use_dsd_format: bool,
        output_mod: bool = False,
    ) -> None:
        output_file: Path = output_folder / self.path
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open("wb") as stream:
            if BestiaryFile.LOOT_FILE_NAME_PATTERN.match(self.name):
                self.dump_strings_to_loot_file(strings, stream)
            else:
                self.dump_strings_to_creature_file(strings, stream)

    def dump_strings_to_creature_file(
        self, strings: StringList, output: BinaryIO
    ) -> None:
        """
        Dumps a list of strings to the main file of a creature entry in the bestiary.

        Args:
            strings (StringList):
                List of strings containing the two creature strings (name & description).
            output (BinaryIO): Binary stream to write to.
        """

        data: EntryData = {}

        for string in strings:
            if not isinstance(string, BestiaryString):
                continue

            if string.bestiary_id.endswith(BestiaryFile.ENTRY_NAME_SUFFIX):
                creature_id: str = string.bestiary_id.removesuffix(
                    BestiaryFile.ENTRY_NAME_SUFFIX
                )
                data[BestiaryFile.ID_KEY] = creature_id

                name_value: str = (
                    string.string if string.string is not None else string.original
                )
                data[BestiaryFile.NAME_KEY] = name_value
            elif string.bestiary_id.endswith(BestiaryFile.ENTRY_DESC_SUFFIX):
                creature_id: str = string.bestiary_id.removesuffix(
                    BestiaryFile.ENTRY_NAME_SUFFIX
                )
                data[BestiaryFile.ID_KEY] = creature_id

                desc_value: str = (
                    string.string if string.string is not None else string.original
                )
                data[BestiaryFile.DESCRIPTION_KEY] = desc_value

        if any(
            key not in data
            for key in [
                BestiaryFile.ID_KEY,
                BestiaryFile.NAME_KEY,
                BestiaryFile.DESCRIPTION_KEY,
            ]
        ):
            raise ValueError(
                "String list does not contain all required strings for a creature entry!"
            )

        output.write(EntryDataAdapter.dump_json(data, indent=4))

    def dump_strings_to_loot_file(self, strings: StringList, output: BinaryIO) -> None:
        """
        Dumps a list of strings to the loot file of a creature entry in the bestiary.

        Args:
            strings (StringList): List of strings containing each loot entry.
            output (BinaryIO): Binary stream to write to.
        """

        data: LootData = {}
        loot_items: list[tuple[str, str]] = []
        data[BestiaryFile.LOOT_KEY] = loot_items

        for string in strings:
            if not isinstance(string, BestiaryString):
                continue

            if BestiaryFile.LOOT_ID_SEP not in string.bestiary_id:
                continue

            text: str = string.string if string.string is not None else string.original
            category: str = string.bestiary_id.split(BestiaryFile.LOOT_ID_SEP, 1)[0]

            loot_items.append((text, category))

        output.write(LootDataAdapter.dump_json(data, indent=4))
