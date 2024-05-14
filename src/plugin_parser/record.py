"""
Copyright (c) Cutleast
"""

import logging
import os
import zlib
from io import BufferedReader, BytesIO

from .datatypes import Flags, Hex, Integer, String
from .subrecord import SUBRECORD_MAPPING, StringSubrecord, Subrecord
from .utilities import PARSE_WHITELIST, get_checksum, peek


class Record:
    """
    Contains parsed record data.
    """

    stream: BufferedReader = None
    header_flags: dict[str, bool] = None
    type: str = "Record"

    subrecords: list[Subrecord] = []

    flag_types = {
        0x00000080: "Localized",
        0x00001000: "Ignored",
        0x00040000: "Compressed",
        0x00000800: "Initially Disabled",
        0x00000020: "Deleted",
        0x00000200: "Light Master",
    }
    flags: dict[str, bool] = {}

    log = logging.getLogger("PluginParser")

    def __init__(self, stream: BufferedReader, header_flags: dict[str, bool]):
        self.stream = stream
        self.header_flags = header_flags

        self.parse()

    def __repr__(self) -> str:
        import pprint

        __dict = self.__dict__.copy()
        __dict.pop("data")
        text = "\n" + pprint.pformat(__dict, indent=4, sort_dicts=False)
        lines: list[str] = []
        for line in text.splitlines():
            line = " " * 4 + line
            lines.append(line)
        return "\n".join(lines)

    def parse(self):
        self.type = String.string(self.stream, 4)
        self.size = Integer.uint32(self.stream)
        self.flags = Flags.flags(self.stream, 4, self.flag_types)
        self.formid = Hex.hex(self.stream, 4)
        self.timestamp = Integer.uint16(self.stream)
        self.version_control_info = Integer.uint16(self.stream)
        self.internal_version = Integer.uint16(self.stream)
        _ = Integer.uint16(self.stream)  # Unknown

        # Decompress data if compressed
        if self.flags["Compressed"]:
            self.decompressed_size = Integer.uint32(self.stream)
            self.data = zlib.decompress(self.stream.read(self.size - 4))
        else:
            self.data = self.stream.read(self.size)

        # Skip parsing if "Ignored" or "Deleted" flag are set
        if self.flags["Ignored"] or self.flags["Deleted"]:
            return

        # Parse subrecords (also known as fields)
        subrecord_stream = BytesIO(self.data)
        if self.type in PARSE_WHITELIST:
            match self.type:
                case "INFO":
                    self.parse_info_record(subrecord_stream)
                case "QUST":
                    self.parse_qust_record(subrecord_stream)
                case _:
                    self.parse_subrecords(subrecord_stream)
        else:
            self.subrecords = []

    def parse_qust_record(self, stream: BytesIO):
        self.subrecords: list[Subrecord] = []

        def get_ctda_hashes():
            hashes: list[int] = []

            while peek(stream, 4) == b"CTDA":
                subrecord = Subrecord(stream, self.header_flags)
                subrecord.parse()

                value = abs(hash(subrecord.data))

                hashes.append(value)

            return hashes

        current_stage_index = 0
        current_entry_index = 0
        current_objective_index = 0

        while subrecord_type := String.string(stream, 4):
            stream.seek(-4, os.SEEK_CUR)

            match subrecord_type:
                # Handle special XXXX subrecords with raw data
                case "XXXX":
                    subrecord_type = String.string(stream, 4)
                    xxxx_size = Integer.uint16(stream)
                    field_size = Integer.uint(stream, xxxx_size)
                    field_type = String.string(stream, 4)
                    field_data = stream.read(field_size)
                    _ = Integer.uint16(stream)
                    subrecord = Subrecord(stream, self.header_flags, field_type)
                    subrecord.size = field_size
                    subrecord.data = field_data

                # Calculate stage "index" from INDX subrecord
                case "INDX":
                    subrecord = Subrecord(stream, self.header_flags)
                    subrecord.parse()

                    current_stage_index = abs(hash(subrecord.data))

                # Calculate log entry "index" from condition hashes
                case "CTDA":
                    hashes = get_ctda_hashes()
                    current_entry_index = sum(hashes)

                # Get log entry string with current log entry index
                case "CNAM":
                    subrecord = StringSubrecord(stream, self.header_flags)
                    subrecord.parse()
                    subrecord.index = get_checksum(
                        current_entry_index - current_stage_index
                    )

                # Get quest objective index
                case "QOBJ":
                    subrecord = Subrecord(stream, self.header_flags)
                    subrecord.parse()

                    current_objective_index = Integer.int16(BytesIO(subrecord.data))

                # Get quest objective string with current objective index
                case "NNAM":
                    subrecord = StringSubrecord(stream, self.header_flags)
                    subrecord.parse()
                    subrecord.index = current_objective_index

                case _:
                    if (
                        subrecord_type in PARSE_WHITELIST[self.type]
                        or subrecord_type == "EDID"
                    ):
                        subrecord: Subrecord = SUBRECORD_MAPPING.get(
                            subrecord_type, Subrecord
                        )(stream, self.header_flags)
                    else:
                        subrecord = Subrecord(stream, self.header_flags)
                    subrecord.parse()

            if subrecord_type in PARSE_WHITELIST[self.type] or subrecord_type == "EDID":
                self.subrecords.append(subrecord)

    def parse_info_record(self, stream: BytesIO):
        self.subrecords: list[Subrecord] = []

        current_index = 0

        while subrecord_type := String.string(stream, 4):
            stream.seek(-4, os.SEEK_CUR)

            match subrecord_type:
                # Handle special XXXX subrecords with raw data
                case "XXXX":
                    subrecord_type = String.string(stream, 4)
                    xxxx_size = Integer.uint16(stream)
                    field_size = Integer.uint(stream, xxxx_size)
                    field_type = String.string(stream, 4)
                    field_data = stream.read(field_size)
                    _ = Integer.uint16(stream)
                    subrecord = Subrecord(stream, self.header_flags, field_type)
                    subrecord.size = field_size
                    subrecord.data = field_data

                # Get response id
                case "TRDT":
                    subrecord = Subrecord(stream, self.header_flags)
                    subrecord.parse()

                    subrecord_stream = BytesIO(subrecord.data)
                    subrecord_stream.seek(12)  # Skip emotion type and value

                    current_index = Integer.uint8(subrecord_stream)

                # Get response string with current reponse id
                case "NAM1":
                    subrecord = StringSubrecord(stream, self.header_flags)
                    subrecord.parse()
                    subrecord.index = current_index
                
                case "DNAM":
                    subrecord = Subrecord(stream, self.header_flags)
                    subrecord.parse()

                    subrecord.formid = Hex.hex(BytesIO(subrecord.data), 4)

                    # self.log.debug(f"Found linked INFO Record {subrecord.formid!r} in {self.type} Record {self.formid!r}.")
                    self.subrecords.append(subrecord)

                case _:
                    if (
                        subrecord_type in PARSE_WHITELIST[self.type]
                        or subrecord_type == "EDID"
                    ):
                        subrecord: Subrecord = SUBRECORD_MAPPING.get(
                            subrecord_type, Subrecord
                        )(stream, self.header_flags)
                    else:
                        subrecord = Subrecord(stream, self.header_flags)
                    subrecord.parse()

            if subrecord_type in PARSE_WHITELIST[self.type] or subrecord_type == "EDID":
                self.subrecords.append(subrecord)

    def parse_subrecords(self, stream: BytesIO):
        self.subrecords: list[Subrecord] = []

        perk_type = None
        epfd_index = 0

        itxt_index = 0

        while subrecord_type := String.string(stream, 4):
            stream.seek(-4, os.SEEK_CUR)

            if subrecord_type == "XXXX":  # Special Subrecords in Cells
                subrecord_type = String.string(stream, 4)
                xxxx_size = Integer.uint16(stream)
                field_size = Integer.uint(stream, xxxx_size)
                field_type = String.string(stream, 4)
                field_data = stream.read(field_size)
                _ = Integer.uint16(stream)
                subrecord = Subrecord(stream, self.header_flags, field_type)
                subrecord.size = field_size
                subrecord.data = field_data

            elif (perk_type == 4 and subrecord_type == "EPF2") or (
                perk_type == 7 and subrecord_type == "EPFD"
            ):
                subrecord = StringSubrecord(stream, self.header_flags)

                if subrecord_type == "EPFD":
                    subrecord.index = epfd_index

                    epfd_index += 1

                else:
                    subrecord.parse()

                    if subrecord.string is None:
                        continue

                    if peek(stream, 4) == b"EPF3":
                        index_subrecord = Subrecord(stream, self.header_flags)
                        index_subrecord.parse()
                        epf2_index = int.from_bytes(
                            index_subrecord.data[2:], byteorder="little"
                        )
                        subrecord.index = epf2_index
                        if subrecord_type in PARSE_WHITELIST[self.type]:
                            self.subrecords.append(subrecord)
                        continue
                    else:
                        self.log.warning(
                            f"EPF2 Subrecord without following EPF3! Record: {self}"
                        )

            elif (
                subrecord_type in SUBRECORD_MAPPING
                and (
                    subrecord_type in PARSE_WHITELIST[self.type]
                    or subrecord_type == "EDID"
                )
                and subrecord_type not in ["EPF2", "EPFD"]
            ):
                subrecord: Subrecord = SUBRECORD_MAPPING[subrecord_type]
                subrecord = subrecord(stream, self.header_flags)

            else:
                subrecord = Subrecord(stream, self.header_flags, subrecord_type)

            subrecord.parse()

            if subrecord_type == "ITXT":
                subrecord.index = itxt_index
                itxt_index += 1

            if self.type == "PERK" and subrecord.type == "EPFT":
                perk_type = Integer.uint8(BytesIO(subrecord.data))

            if subrecord_type in PARSE_WHITELIST[self.type] or subrecord_type == "EDID":
                self.subrecords.append(subrecord)
