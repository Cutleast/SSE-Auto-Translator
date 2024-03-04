"""
Copyright (c) Cutleast
"""

import os
import zlib
from io import BufferedReader, BytesIO

from .datatypes import Flags, Hex, Integer, String
from .subrecord import SUBRECORD_MAPPING, Subrecord, StringSubrecord
from .utilities import PARSE_WHITELIST, peek, get_checksum


class Record:
    """
    Contains parsed record data.
    """

    stream: BufferedReader
    type: str = "Record"

    subrecords: list[Subrecord] = []

    flag_types = {
        0x00000080: "Localized",
        0x00001000: "Ignored",
        0x00040000: "Compressed",
        0x00000800: "Initially Disabled",
        0x00000020: "Deleted",
    }
    flags: dict[str, bool] = {}

    def __init__(self, stream: BufferedReader):
        self.stream = stream

        self.parse()

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
                subrecord = Subrecord(stream)
                subrecord.parse(self.flags)

                value = abs(hash(subrecord.data))

                hashes.append(value)

            return hashes

        current_stage_index = 0
        current_entry_index = 0
        current_objective_index = 0

        while subrecord_type := String.string(stream, 4):
            stream.seek(-4, os.SEEK_CUR)

            match subrecord_type:
                # Calculate stage "index" from INDX subrecord
                case "INDX":
                    subrecord = Subrecord(stream)
                    subrecord.parse(self.flags)

                    current_stage_index = abs(hash(subrecord.data))

                # Calculate log entry "index" from condition hashes
                case "CTDA":
                    hashes = get_ctda_hashes()
                    current_entry_index = sum(hashes)

                # Get log entry string with current log entry index
                case "CNAM":
                    subrecord = StringSubrecord(stream)
                    subrecord.parse(self.flags)
                    subrecord.index = get_checksum(
                        current_entry_index - current_stage_index
                    )

                # Get quest objective index
                case "QOBJ":
                    subrecord = Subrecord(stream)
                    subrecord.parse(self.flags)

                    current_objective_index = Integer.int16(BytesIO(subrecord.data))

                # Get quest objective string with current objective index
                case "NNAM":
                    subrecord = StringSubrecord(stream)
                    subrecord.parse(self.flags)
                    subrecord.index = current_objective_index

                case _:
                    subrecord: Subrecord = SUBRECORD_MAPPING.get(
                        subrecord_type, Subrecord
                    )(stream)
                    subrecord.parse(self.flags)

            if subrecord_type in PARSE_WHITELIST[self.type] or subrecord_type == "EDID":
                self.subrecords.append(subrecord)

    def parse_info_record(self, stream: BytesIO):
        self.subrecords: list[Subrecord] = []

        current_index = 0

        while subrecord_type := String.string(stream, 4):
            stream.seek(-4, os.SEEK_CUR)

            match subrecord_type:
                # Get response id
                case "TRDT":
                    subrecord = Subrecord(stream)
                    subrecord.parse(self.flags)

                    subrecord_stream = BytesIO(subrecord.data)
                    subrecord_stream.seek(12)  # Skip emotion type and value

                    current_index = Integer.uint8(subrecord_stream)

                # Get response string with current reponse id
                case "NAM1":
                    subrecord = StringSubrecord(stream)
                    subrecord.parse(self.flags)
                    subrecord.index = current_index

                case _:
                    subrecord: Subrecord = SUBRECORD_MAPPING.get(
                        subrecord_type, Subrecord
                    )(stream)
                    subrecord.parse(self.flags)

            if subrecord_type in PARSE_WHITELIST[self.type] or subrecord_type == "EDID":
                self.subrecords.append(subrecord)

    def parse_subrecords(self, stream: BytesIO):
        self.subrecords: list[Subrecord] = []

        perk_type = None
        perk_index = 0

        while subrecord_type := String.string(stream, 4):
            stream.seek(-4, os.SEEK_CUR)

            if subrecord_type == "XXXX":  # Special Subrecords in Cells
                subrecord_type = String.string(stream, 4)
                xxxx_size = Integer.uint16(stream)
                field_size = Integer.uint(stream, xxxx_size)
                field_type = String.string(stream, 4)
                field_data = stream.read(field_size)
                _ = Integer.uint16(stream)
                subrecord = Subrecord(stream, field_type)
                subrecord.size = field_size
                subrecord.data = field_data

            elif (perk_type == 4 and subrecord_type == "EPF2") or (
                perk_type == 7 and subrecord_type == "EPFD"
            ):
                subrecord = StringSubrecord(stream)
                subrecord.index = perk_index

                perk_index += 1

            elif subrecord_type in SUBRECORD_MAPPING:
                subrecord: Subrecord = SUBRECORD_MAPPING[subrecord_type]
                subrecord = subrecord(stream)

            else:
                subrecord = Subrecord(stream, subrecord_type)

            subrecord.parse(self.flags)

            if self.type == "PERK" and subrecord.type == "EPFT":
                perk_type = Integer.uint8(BytesIO(subrecord.data))

            if subrecord_type in PARSE_WHITELIST[self.type] or subrecord_type == "EDID":
                self.subrecords.append(subrecord)
