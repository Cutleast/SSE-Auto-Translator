"""
Copyright (c) Cutleast
"""

from __future__ import annotations

import logging
from enum import IntEnum
from io import BytesIO

from .datatypes import Hex, Integer
from .flags import RecordFlags
from .record import Record
from .utilities import Stream, peek, prettyprint_object

log = logging.getLogger("PluginParser.Group")


class Group:
    """
    Class for GRUP records.
    """

    type: str
    group_size: int
    label: str
    group_type: int
    timestamp: int
    version_control_info: int
    unknown: int
    data: bytes

    children: list[Group | Record]

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

    def __repr__(self) -> str:
        return prettyprint_object(self)

    def __len__(self) -> int:
        return len(self.dump())

    def parse(self, stream: Stream, header_flags: RecordFlags) -> None:
        self.type = stream.read(4).decode()
        self.group_size = Integer.parse(stream, Integer.IntType.UInt32)
        label = stream.read(4)
        self.group_type = Integer.parse(stream, Integer.IntType.Int32)
        self.timestamp = Integer.parse(stream, Integer.IntType.UInt16)
        self.version_control_info = Integer.parse(stream, Integer.IntType.UInt16)
        self.unknown = Integer.parse(stream, Integer.IntType.UInt32)

        self.data = stream.read(self.group_size - 24)
        record_stream = BytesIO(self.data)

        match self.group_type:
            # Normal groups
            case Group.GroupType.Normal:
                self.label = label.decode()
                self.parse_records(record_stream, header_flags)

            # Dialogue Groups
            case Group.GroupType.TopicChildren:
                self.label = Hex.parse(label)
                self.parse_records(record_stream, header_flags)

            # Worldspace Group
            case Group.GroupType.WorldChildren:
                self.label = Hex.parse(label)
                self.parse_records(record_stream, header_flags)

            # Exterior Cells
            case Group.GroupType.ExteriorCellBlock:
                label_stream = BytesIO(label)
                self.grid = (
                    Integer.parse(label_stream, Integer.IntType.Int16),  # Y
                    Integer.parse(label_stream, Integer.IntType.Int16),  # X
                )
                self.parse_records(record_stream, header_flags)

            case Group.GroupType.ExteriorCellSubBlock:
                label_stream = BytesIO(label)
                self.grid = (
                    Integer.parse(label_stream, Integer.IntType.Int16),  # Y
                    Integer.parse(label_stream, Integer.IntType.Int16),  # X
                )
                self.parse_records(record_stream, header_flags)

            # Interior Cells
            case Group.GroupType.InteriorCellBlock:
                self.block_number = Integer.parse(label, Integer.IntType.Int32)
                self.parse_records(record_stream, header_flags)

            case Group.GroupType.InteriorCellSubBlock:
                self.subblock_number = Integer.parse(label, Integer.IntType.Int32)
                self.parse_records(record_stream, header_flags)

            # Cell Children
            case (
                Group.GroupType.CellChildren
                | Group.GroupType.CellPersistentChildren
                | Group.GroupType.CellTemporaryChildren
            ):
                self.parent_cell = Hex.parse(label)
                self.parse_records(record_stream, header_flags)

            # Unknown
            case self.unknown:
                log.warning(f"Unknown Group Type: {self.group_type}")
                raise Exception(f"Unknown Group Type: {self.group_type}")

    def parse_records(self, stream: Stream, header_flags: RecordFlags) -> None:
        self.children = []

        while child_type := peek(stream, 4):
            child_type_name = child_type.decode()

            child: Group | Record
            if child_type_name == "GRUP":
                child = Group()
            else:
                child = Record()

            child.parse(stream, header_flags)
            self.children.append(child)

    def dump(self) -> bytes:
        data = b""

        child_data = b"".join(child.dump() for child in self.children)
        self.group_size = (
            len(child_data) + 24
        )  # Size of subgroups and records including Group Header

        data += self.type.encode()
        data += Integer.dump(self.group_size, Integer.IntType.UInt32)

        match self.group_type:
            case Group.GroupType.Normal:
                data += self.label.encode()

            case Group.GroupType.WorldChildren | Group.GroupType.TopicChildren:
                # print(self.group_type)
                data += Hex.dump(self.label)

            # Cell Children
            case (
                Group.GroupType.CellChildren
                | Group.GroupType.CellPersistentChildren
                | Group.GroupType.CellTemporaryChildren
            ):
                data += Hex.dump(self.parent_cell)

            case (
                Group.GroupType.ExteriorCellBlock
                | Group.GroupType.ExteriorCellSubBlock
            ):
                data += Integer.dump(self.grid[0], Integer.IntType.Int16)  # Y
                data += Integer.dump(self.grid[1], Integer.IntType.Int16)  # X

            case Group.GroupType.InteriorCellBlock:
                data += Integer.dump(self.block_number, Integer.IntType.Int32)

            case Group.GroupType.InteriorCellSubBlock:
                data += Integer.dump(self.subblock_number, Integer.IntType.Int32)

        data += Integer.dump(self.group_type, Integer.IntType.Int32)
        data += Integer.dump(self.timestamp, Integer.IntType.UInt16)
        data += Integer.dump(self.version_control_info, Integer.IntType.UInt16)
        data += Integer.dump(self.unknown, Integer.IntType.UInt32)
        data += child_data

        return data
