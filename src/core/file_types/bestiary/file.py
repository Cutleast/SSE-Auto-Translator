"""
Copyright (c) Cutleast
"""

import re
from enum import Enum, auto
from pathlib import Path
from typing import Any, BinaryIO, ClassVar, Optional, TypeAlias, override

from cutleast_core_lib.core.utilities.reference_dict import ReferenceDict
from pydantic import TypeAdapter, ValidationError
from PySide6.QtWidgets import QApplication

from core.file_source.file_source import FileSource
from core.file_source.file_source_factory import FileSourceFactory
from core.mod_file.context import ModFileContext
from core.mod_file.mod_file import ModFile
from core.string.string_status import StringStatus
from core.string.types import String, StringList
from core.translation_context.context_property import ContextProperty
from core.translation_context.related_string import RelatedString

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

    class EntryKind(Enum):
        """
        Kinds of strings in a creature entry of the bestiary.
        """

        Name = auto()
        """The name of the creature."""

        Description = auto()
        """The description of the creature."""

        Loot = auto()
        """An item that the creature drops."""

        def get_localized_name(self) -> str:
            """
            Gets the localized name of this kind.

            Returns:
                str: The localized name.
            """

            match self:
                case BestiaryFile.EntryKind.Name:
                    return QApplication.translate("BestiaryFile", "Creature name")
                case BestiaryFile.EntryKind.Description:
                    return QApplication.translate("BestiaryFile", "Creature description")
                case BestiaryFile.EntryKind.Loot:
                    return QApplication.translate("BestiaryFile", "Loot item")

    LOOT_KEY: ClassVar[str] = "loot"
    """Name of the key attribute in a bestiary loot file."""

    ID_KEY: ClassVar[str] = "id"
    """Name of the id attribute in a bestiary creature file."""

    NAME_KEY: ClassVar[str] = "name"
    """Name of the name attribute in a bestiary creature file."""

    DESCRIPTION_KEY: ClassVar[str] = "description"
    """Name of the description attribute in a bestiary creature file."""

    LOOT_FILE_NAME_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"[a-z \-_]+_LOOT *\.json", re.IGNORECASE
    )
    """Pattern for the file name of bestiary loot files."""

    RESIST_FILE_NAME_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"[a-z \-_]+_RESIST *\.json", re.IGNORECASE
    )
    """Pattern for the file name of bestiary resistance files."""

    ENTRY_NAME_SUFFIX: ClassVar[str] = "-name"
    """ID suffix for identifying the name string of an entry file."""

    ENTRY_DESC_SUFFIX: ClassVar[str] = "-description"
    """ID suffix for identifying the description string of an entry file."""

    LOOT_ID_SEP: ClassVar[str] = "_LOOT"
    """ID separator for identifying the category of a loot item."""

    LOOT_ID_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        rf"(?P<creature>.*?){LOOT_ID_SEP}-(?P<index>[0-9]+)/(?P<count>[0-9]+)-"
        "(?P<category>.*)"
    )
    """
    Pattern for the ID of a loot item string.
    
    Named groups:
        creature: ID of the creature this loot item belongs to.
        index:
            Index of this loot item in the list of loot items for the current creature
            (starting with 0).
        count: Total number of loot items for the current creature.
        category: Category of this loot item (e.g. "food", "weapon", etc.).
    """

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

        file_source: FileSource = FileSourceFactory.for_file_path(self.full_path)
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
    def extract_strings_from_loot_file(creature_id: str, stream: BinaryIO) -> StringList:
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

            creature_id: str
            if string.bestiary_id.endswith(BestiaryFile.ENTRY_NAME_SUFFIX):
                creature_id = string.bestiary_id.removesuffix(
                    BestiaryFile.ENTRY_NAME_SUFFIX
                )
                data[BestiaryFile.ID_KEY] = creature_id

                name_value: str = (
                    string.string if string.string is not None else string.original
                )
                data[BestiaryFile.NAME_KEY] = name_value
            elif string.bestiary_id.endswith(BestiaryFile.ENTRY_DESC_SUFFIX):
                creature_id = string.bestiary_id.removesuffix(
                    BestiaryFile.ENTRY_DESC_SUFFIX
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

            match: Optional[re.Match[str]] = BestiaryFile.LOOT_ID_PATTERN.match(
                string.bestiary_id
            )
            if match is None:
                continue

            text: str = string.string if string.string is not None else string.original
            category: str = match.group("category")

            loot_items.append((text, category))

        output.write(LootDataAdapter.dump_json(data, indent=4))

    @override
    @classmethod
    def get_string_contexts(
        cls,
        mod_file_path: Path,
        strings: StringList,
        all_strings: dict[Path, StringList],
    ) -> ReferenceDict[String, ModFileContext]:
        # Each creature has its own folder containing its entry file and its loot file.
        folder_strings: list[tuple[Path, BestiaryString]] = [
            (path, string)
            for path, file_strings in all_strings.items()
            if path.parent == mod_file_path.parent
            for string in file_strings
            if isinstance(string, BestiaryString)
        ]

        contexts: ReferenceDict[String, ModFileContext] = ReferenceDict()
        for string in strings:
            if isinstance(string, BestiaryString):
                contexts[string] = BestiaryFile.__get_string_context(
                    string, folder_strings
                )

        return contexts

    @staticmethod
    def __get_string_context(
        string: BestiaryString, folder_strings: list[tuple[Path, BestiaryString]]
    ) -> ModFileContext:
        """
        Builds the context for a single bestiary string.

        Args:
            string (BestiaryString): String to build the context for.
            folder_strings (list[tuple[Path, BestiaryString]]):
                All strings of the creature's folder with their mod file paths.

        Returns:
            ModFileContext: The context for the string.
        """

        kind: Optional[BestiaryFile.EntryKind] = BestiaryFile.get_entry_kind(
            string.bestiary_id
        )
        if kind is None:
            return ModFileContext()

        related_kinds: list[BestiaryFile.EntryKind]
        properties: list[ContextProperty] = []
        match kind:
            case BestiaryFile.EntryKind.Name:
                related_kinds = [BestiaryFile.EntryKind.Description]
            case BestiaryFile.EntryKind.Description:
                related_kinds = [BestiaryFile.EntryKind.Name]
            case BestiaryFile.EntryKind.Loot:
                related_kinds = [
                    BestiaryFile.EntryKind.Name,
                    BestiaryFile.EntryKind.Loot,
                ]
                properties = BestiaryFile.__get_loot_properties(string.bestiary_id)

        related_strings: list[RelatedString] = []
        for path, folder_string in folder_strings:
            folder_kind: Optional[BestiaryFile.EntryKind] = BestiaryFile.get_entry_kind(
                folder_string.bestiary_id
            )
            if folder_string.id == string.id or folder_kind not in related_kinds:
                continue

            related_strings.append(
                RelatedString(
                    relation=folder_kind.get_localized_name(),
                    string=folder_string,
                    mod_file=path,
                )
            )

        return ModFileContext(
            string_kind=QApplication.translate("BestiaryFile", "Bestiary")
            + " - "
            + kind.get_localized_name(),
            properties=properties,
            related_strings=related_strings,
        )

    @staticmethod
    def __get_loot_properties(bestiary_id: str) -> list[ContextProperty]:
        """
        Gets the category and the position of a loot item from its ID.

        Args:
            bestiary_id (str): ID of the loot item string.

        Returns:
            list[ContextProperty]: The category and the position of the loot item.
        """

        match: Optional[re.Match[str]] = BestiaryFile.LOOT_ID_PATTERN.match(bestiary_id)
        if match is None:
            return []

        return [
            ContextProperty(
                label=QApplication.translate("BestiaryFile", "Category"),
                value=match.group("category"),
            ),
            ContextProperty(
                label=QApplication.translate("BestiaryFile", "Position"),
                value=f"{int(match.group('index')) + 1}/{match.group('count')}",
            ),
        ]

    @staticmethod
    def get_entry_kind(bestiary_id: str) -> Optional[BestiaryFile.EntryKind]:
        """
        Determines the kind of a bestiary string from its ID.

        Args:
            bestiary_id (str): ID of the bestiary string.

        Returns:
            Optional[EntryKind]: The kind of the string or None if it is unknown.
        """

        if BestiaryFile.LOOT_ID_PATTERN.match(bestiary_id):
            return BestiaryFile.EntryKind.Loot

        if bestiary_id.endswith(BestiaryFile.ENTRY_NAME_SUFFIX):
            return BestiaryFile.EntryKind.Name

        if bestiary_id.endswith(BestiaryFile.ENTRY_DESC_SUFFIX):
            return BestiaryFile.EntryKind.Description

        return None
