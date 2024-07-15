"""
Copyright (c) Cutleast
"""

import logging
from io import BufferedReader
from pathlib import Path

from utilities.string import String as PluginString

from . import utilities as utils
from .datatypes import RawString
from .flags import RecordFlags
from .group import Group
from .record import Record
from .subrecord import EDID, MAST, StringSubrecord


class Plugin:
    """
    Contains parsed plugin data.
    """

    path: Path

    header: Record
    groups: list[Group]

    __string_subrecords: dict[PluginString, StringSubrecord] = None

    log = logging.getLogger("PluginInterface")

    def __init__(self, path: Path):
        self.path = path

        self.load()

    def __repr__(self) -> str:
        return utils.prettyprint_object(self)

    def __len__(self):
        return len(self.dump())

    def __str__(self) -> str:
        return self.__repr__()

    def load(self):
        with self.path.open("rb") as stream:
            self.parse(stream)

    def parse(self, stream: BufferedReader):
        self.log.info(f"Parsing {str(self.path)!r}...")

        self.groups = []

        self.header = Record()
        self.header.parse(stream, [])

        self.masters = [
            subrecord.file
            for subrecord in self.header.subrecords
            if isinstance(subrecord, MAST)
        ]

        while utils.peek(stream, 1):
            group = Group()
            group.parse(stream, self.header.flags)
            self.groups.append(group)

        self.log.info("Parsing complete.")

    def dump(self):
        data = b""

        data += self.header.dump()

        for group in self.groups:
            data += group.dump()

        return data

    def save(self):
        self.path.write_bytes(self.dump())

    @staticmethod
    def get_record_edid(record: Record):
        try:
            for subrecord in record.subrecords:
                if isinstance(subrecord, EDID):
                    return subrecord.editor_id
        except AttributeError:
            return None

    def extract_group_strings(
        self, group: Group, extract_localized: bool = False, unfiltered: bool = False
    ):
        """
        Extracts strings from parsed <group>.
        """

        strings: dict[PluginString, StringSubrecord] = {}

        record: Record | Group
        for record in group.children:
            if isinstance(record, Group):
                strings |= self.extract_group_strings(record, extract_localized)
            else:
                edid = self.get_record_edid(record)
                master_index = int(record.formid[:2], base=16)

                # Get plugin that first defines this record from masters
                try:
                    master = self.masters[master_index]
                # If index is not in masters, then the record is first defined in this plugin
                except IndexError:
                    master = self.path.name

                formid = f"{record.formid}|{master}"

                # Replace Master Index by "FE" Prefix to indicate Light Plugin
                # This is especially relevant for DSD
                # if (
                #     self.path.suffix.lower() == ".esl"
                #     or RecordFlags.LightMaster in self.header.flags
                # ) and master == self.path.name:
                #     formid = "FE" + formid[2:]

                for subrecord in record.subrecords:
                    if isinstance(subrecord, StringSubrecord):
                        string: RawString | int = subrecord.string

                        if (isinstance(string, RawString) or extract_localized) and (
                            utils.is_valid_string(string) or unfiltered
                        ):
                            string_data = PluginString(
                                edid,
                                formid,
                                subrecord.index,
                                f"{record.type} {subrecord.type}",
                                original_string=str(string),
                                status=(
                                    PluginString.Status.TranslationRequired
                                    if utils.is_valid_string(string)
                                    else PluginString.Status.NoTranslationRequired
                                ),
                            )

                            strings[string_data] = subrecord

        return strings

    def extract_strings(
        self, extract_localized: bool = False, unfiltered: bool = False
    ):
        """
        Extracts strings from parsed plugin.

        Only returns strings that pass a filter if `unfiltered` is False.
        """

        strings: list[PluginString] = []

        for group in self.groups:
            current_group: list[PluginString] = list(
                self.extract_group_strings(group, extract_localized, unfiltered).keys()
            )
            strings += current_group

        return strings

    def find_string_subrecord(
        self, form_id: str, type: str, string: str, index: int | None
    ) -> StringSubrecord | None:
        """
        Finds subrecord that matches the given parameters.
        """

        if self.__string_subrecords is None:
            string_subrecords: dict[PluginString, StringSubrecord] = {}

            for group in self.groups:
                current_group = self.extract_group_strings(group)
                string_subrecords |= current_group

            self.__string_subrecords = string_subrecords

        for plugin_string, subrecord in self.__string_subrecords.items():
            if (
                plugin_string.form_id[2:]
                == form_id[2:]  # Ignore master index and FE prefix
                and plugin_string.type == type
                and plugin_string.original_string == string
                and plugin_string.index == index
            ):
                return subrecord

    def replace_strings(self, strings: list[PluginString]):
        """
        Replaces strings in plugin by `strings`.
        """

        for string in strings:
            subrecord = self.find_string_subrecord(
                string.form_id, string.type, string.original_string, string.index
            )

            if subrecord:
                subrecord.set_string(string.translated_string)
            else:
                self.log.error(
                    f"Failed to replace string {string}: Subrecord not found!"
                )

    @staticmethod
    def extract_group_records(group: Group, recursive: bool = True):
        """
        Returns all records from `group`
        and records from child groups if `recursive` is `True`.
        """

        records: list[Record] = []

        for child in group.children:
            if isinstance(child, Record):
                records.append(child)
            elif isinstance(child, Group) and recursive:
                records.extend(Plugin.extract_group_records(child, recursive))

        return records

    def eslify_formids(self):
        """
        Recounts FormIDs beginning with `0x800`.
        """

        records = [
            record
            for group in self.groups
            for record in Plugin.extract_group_records(group)
        ]

        cur_formid = 0x800
        for record in records:
            # Ignore records from external masters
            if int(record.formid[:2], base=16) >= len(self.masters):
                new_formid = record.formid[:-3] + hex(cur_formid)[-3:]
                record.formid = new_formid

                cur_formid += 1
    
    def eslify_plugin(self):
        """
        Recounts FormIDs and sets Light Flag in Header.
        """

        if RecordFlags.LightMaster in self.header.flags:
            return
        
        self.eslify_formids()
        self.header.flags |= RecordFlags.LightMaster

    @staticmethod
    def is_light(plugin_path: Path):
        """
        Checks if `plugin_path` is a light plugin.
        This is indicated either by the file extension (.esl)
        or the light flag in the header.
        """

        if plugin_path.suffix.lower() == ".esl":
            return True

        with plugin_path.open("rb") as stream:
            header = Record()
            header.parse(stream, [])

        return RecordFlags.LightMaster in header.flags
