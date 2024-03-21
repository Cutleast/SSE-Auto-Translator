"""
Copyright (c) Cutleast
"""

import logging
import os
from enum import IntEnum
from io import BufferedReader, BytesIO

from .datatypes import Hex, Integer, String
from .record import Record
from .utilities import PARSE_WHITELIST

log = logging.getLogger("PluginParser.Group")


class Group:
    """
    Class for GRUP records.
    """

    type = "GRUP"
    stream: BufferedReader = None
    header_flags: dict[str, bool] = None
    records: list[Record] = None

    class GroupType(IntEnum):
        """
        Group types. See https://en.uesp.net/wiki/Skyrim_Mod:Mod_File_Format#Groups for more.
        """

        Normal = 0  # Regular Record
        WorldChildren = 1  # Worldspace
        InteriorCellBlock = 2  # Interior Cell
        InteriorCellSubBlock = 3  # Interior Cell
        ExteriorCellBlock = 4  # Exterior Cell
        ExteriorCellSubBlock = 5  # Exterior Cell
        CellChildren = 6  # Cell Record
        TopicChildren = 7  # Dialogue
        CellPersistentChildren = 8  # Persistent Cell Record
        CellTemporaryChildren = 9  # Temporary Cell Record

    def __init__(self, stream: BufferedReader, header_flags: dict[str, bool]):
        self.stream = stream
        self.header_flags = header_flags

        self.parse()
    
    def __repr__(self) -> str:
        import pprint

        _dict = self.__dict__.copy()
        _dict.pop("parent")
        _dict.pop("data")

        return "\n" + pprint.pformat(_dict, indent=4, sort_dicts=False)

    def __repr__(self) -> str:
        import pprint

        _dict = self.__dict__.copy()
        _dict.pop("parent")
        _dict.pop("data")

        return "\n" + pprint.pformat(_dict, indent=4, sort_dicts=False)

    def __len__(self):
        try:
            if self.group_size >= 24:
                return self.group_size - 24
            else:
                return self.group_size
        except AttributeError:
            return 0

    def parse(self):
        self.type = String.string(self.stream, 4)
        self.group_size = Integer.uint32(self.stream)
        self.label = self.stream.read(4)
        self.group_type = Integer.int32(self.stream)
        self.timestamp = Integer.uint16(self.stream)
        self.version_control_info = Integer.uint16(self.stream)
        _ = Integer.uint32(self.stream)

        self.data = self.stream.read(len(self))

        match self.group_type:
            # Normal groups
            case Group.GroupType.Normal:
                self.label = String.string(BytesIO(self.label), 4)

                if self.label in PARSE_WHITELIST:
                    record_stream = BytesIO(self.data)
                    self.parse_records(record_stream)
                else:
                    self.records = []

            # Dialogue Groups
            case Group.GroupType.TopicChildren:
                self.label = Hex.hex(BytesIO(self.label), 4)

                if "DIAL" in PARSE_WHITELIST:
                    record_stream = BytesIO(self.data)
                    self.parse_records(record_stream)
                else:
                    self.records = []

            # Worldspace Group
            case Group.GroupType.WorldChildren:
                self.label = Hex.hex(BytesIO(self.label), 4)
                self.parse_records(BytesIO(self.data))

            # Exterior Cells
            case Group.GroupType.ExteriorCellBlock:
                label_stream = BytesIO(self.label)
                self.grid = (
                    Integer.int16(label_stream),  # Y
                    Integer.int16(label_stream),  # X
                )
                self.parse_records(BytesIO(self.data))

            case Group.GroupType.ExteriorCellSubBlock:
                label_stream = BytesIO(self.label)
                self.grid = (
                    Integer.int16(label_stream),  # Y
                    Integer.int16(label_stream),  # X
                )
                self.parse_records(BytesIO(self.data))

            # Interior Cells
            case Group.GroupType.InteriorCellBlock:
                self.block_number = Integer.int32(BytesIO(self.label))
                self.parse_records(BytesIO(self.data))

            case Group.GroupType.InteriorCellSubBlock:
                self.subblock_number = Integer.int32(BytesIO(self.label))
                self.parse_records(BytesIO(self.data))

            # Cell Children
            case Group.GroupType.CellChildren:
                self.label = Hex.hex(BytesIO(self.label), 4)
                self.parse_records(BytesIO(self.data))

            case Group.GroupType.CellPersistentChildren:
                self.parent_cell = Hex.hex(BytesIO(self.label), 4)
                self.parse_records(BytesIO(self.data))

            case Group.GroupType.CellTemporaryChildren:
                self.parent_cell = Hex.hex(BytesIO(self.label), 4)
                self.parse_records(BytesIO(self.data))

            # Unknown
            case _:
                log.warning("Unknown Group Type:", self.group_type)

        return self

    def parse_records(self, stream: BytesIO):
        self.records: list[Record] = []

        while record_type := String.string(stream, 4):
            stream.seek(-4, os.SEEK_CUR)
            if record_type == "GRUP":
                record = Group(stream, self.header_flags)
            else:
                record = Record(stream, self.header_flags)

            self.records.append(record)

        return self
