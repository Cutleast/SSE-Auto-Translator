"""
Copyright (c) Cutleast
"""

import logging
import zlib
from io import BytesIO
from typing import Optional, override

from .datatypes import Hex, Integer
from .flags import RecordFlags
from .subrecord import EPFT, SUBRECORD_MAP, TRDT, StringSubrecord, Subrecord
from .utilities import STRING_RECORDS, Stream, get_checksum, peek, prettyprint_object


class Record:
    """
    Contains parsed record data.
    """

    type: str
    size: int
    flags: RecordFlags
    formid: str
    timestamp: int
    version_control_info: int
    internal_version: int
    unknown: int
    data: bytes

    subrecords: list[Subrecord]

    log = logging.getLogger("PluginParser")

    @override
    def __repr__(self) -> str:
        return prettyprint_object(self)

    def __len__(self) -> int:
        return len(self.dump())

    def parse(self, stream: Stream, header_flags: RecordFlags) -> None:
        self.type = stream.read(4).decode()
        self.size = Integer.parse(stream, Integer.IntType.UInt32)
        self.flags = RecordFlags.parse(stream, Integer.IntType.UInt32)
        self.formid = Hex.parse(stream)
        self.timestamp = Integer.parse(stream, Integer.IntType.UInt16)
        self.version_control_info = Integer.parse(stream, Integer.IntType.UInt16)
        self.internal_version = Integer.parse(stream, Integer.IntType.UInt16)
        self.unknown = Integer.parse(stream, Integer.IntType.UInt16)

        # Decompress data if compressed
        if RecordFlags.Compressed in self.flags:
            decompressed_size = Integer.parse(stream, Integer.IntType.UInt32)
            self.data = zlib.decompress(stream.read(self.size - 4))
            self.size = decompressed_size
        else:
            self.data = stream.read(self.size)

        # Parse subrecords (also known as fields)
        match self.type:
            case "INFO":
                self.parse_info_record(header_flags)
            case "PERK":
                self.parse_perk_record(header_flags)
            case "QUST":
                self.parse_qust_record(header_flags)
            case _:
                self.parse_subrecords(header_flags)

    def parse_qust_record(self, header_flags: RecordFlags) -> None:
        stream = BytesIO(self.data)
        self.subrecords = []

        def calc_condition_index() -> int:
            """
            Creates unique index from hashes of previous block
            of CTDA subrecords and previous INDX subrecord.

            Returns hash of INDX subrecord if there is no CTDA block.
            """

            # Get previous block of CTDA subrecords
            # after previous INDX subrecord
            ctda_subrecords: list[Subrecord] = []
            indx_subrecord: Optional[Subrecord] = None

            for subrecord in self.subrecords[::-1]:
                if subrecord.type == "CTDA":
                    ctda_subrecords.append(subrecord)

                # Break if INDX subrecord is reached
                elif subrecord.type == "INDX":
                    indx_subrecord = subrecord
                    break

                # Only break if INDX subrecord is reached
                elif ctda_subrecords and indx_subrecord is not None:
                    break

            if indx_subrecord is None:
                raise ValueError(f"No INDX subrecord found in record {self.formid}!")

            stage_index = abs(hash(indx_subrecord.data))

            if not ctda_subrecords:
                return get_checksum(stage_index)

            # Bring CTDA subrecords back in original order
            ctda_subrecords.reverse()

            hash_value: int = 0
            for subrecord in ctda_subrecords:
                value = abs(hash(subrecord.data))
                hash_value += value

            index = get_checksum(hash_value - stage_index)

            return index

        current_objective_index = 0

        while stream.tell() < len(self.data):
            subrecord_type = peek(stream, 4).decode()

            subrecord: Subrecord
            if subrecord_type in STRING_RECORDS.get(self.type, []):
                subrecord = StringSubrecord(subrecord_type)
            else:
                subrecord = SUBRECORD_MAP.get(subrecord_type, Subrecord)()

            subrecord.parse(stream, header_flags)
            self.subrecords.append(subrecord)

            match subrecord_type:
                # Set current log entry index as index of string
                case "CNAM":
                    subrecord.index = calc_condition_index()

                # Get quest objective index
                case "QOBJ":
                    current_objective_index = subrecord.index or 0

                # Set current objective index as index of string
                case "NNAM":
                    subrecord.index = current_objective_index

    def parse_info_record(self, header_flags: RecordFlags) -> None:
        stream = BytesIO(self.data)
        self.subrecords = []
        current_index = 0

        while stream.tell() < len(self.data):
            subrecord_type = peek(stream, 4).decode()

            subrecord: Subrecord
            if subrecord_type in STRING_RECORDS.get(self.type, []):
                subrecord = StringSubrecord(subrecord_type)
            else:
                subrecord = SUBRECORD_MAP.get(subrecord_type, Subrecord)()

            subrecord.parse(stream, header_flags)

            # Get response id
            if isinstance(subrecord, TRDT):
                current_index = subrecord.response_id
            # Set current response id as index of string
            elif subrecord_type == "NAM1":
                subrecord.index = current_index

            self.subrecords.append(subrecord)

    def parse_perk_record(self, header_flags: RecordFlags) -> None:
        stream = BytesIO(self.data)
        self.subrecords = []

        perk_type = None
        epfd_index = 0

        while stream.tell() < len(self.data):
            subrecord_type = peek(stream, 4).decode()

            subrecord: Subrecord
            if (
                (perk_type == 4 and subrecord_type == "EPF2")
                or (perk_type == 7 and subrecord_type == "EPFD")
                or (
                    subrecord_type in STRING_RECORDS.get(self.type, [])
                    and subrecord_type not in ["EPF2", "EPFD"]
                )
            ):
                subrecord = StringSubrecord(subrecord_type)
            else:
                subrecord = SUBRECORD_MAP.get(subrecord_type, Subrecord)()

            subrecord.parse(stream, header_flags)
            self.subrecords.append(subrecord)

            if isinstance(subrecord, EPFT):
                perk_type = subrecord.perk_type

            elif subrecord_type == "EPFD":
                subrecord.index = epfd_index
                epfd_index += 1

            elif subrecord_type == "EPF2":
                if peek(stream, 4) == b"EPF3":
                    index_subrecord = Subrecord()
                    index_subrecord.parse(stream, header_flags)
                    epf2_index = int.from_bytes(
                        index_subrecord.data[2:], byteorder="little"
                    )
                    subrecord.index = epf2_index
                    self.subrecords.append(index_subrecord)

                else:
                    self.log.warning(
                        f"EPF2 Subrecord without following EPF3! Record: {self}"
                    )

    def parse_subrecords(self, header_flags: RecordFlags) -> None:
        stream = BytesIO(self.data)
        self.subrecords = []
        itxt_index = 0

        while stream.tell() < len(self.data):
            subrecord_type = peek(stream, 4).decode()

            subrecord: Subrecord
            if subrecord_type in STRING_RECORDS.get(self.type, []):
                subrecord = StringSubrecord(subrecord_type)
            else:
                subrecord = SUBRECORD_MAP.get(subrecord_type, Subrecord)()

            subrecord.parse(stream, header_flags)

            if subrecord.type == "ITXT":
                subrecord.index = itxt_index
                itxt_index += 1

            self.subrecords.append(subrecord)

    def dump(self) -> bytes:
        # Prepare Data field
        data = b"".join(subrecord.dump() for subrecord in self.subrecords)

        if RecordFlags.Compressed in self.flags:
            uncompressed_size = Integer.dump(len(data), Integer.IntType.UInt32)
            data = uncompressed_size + zlib.compress(data)

        self.size = len(data)

        # Combine all values
        self.data = b""
        self.data += self.type.encode()
        self.data += Integer.dump(self.size, Integer.IntType.UInt32)
        self.data += RecordFlags.dump(self.flags, Integer.IntType.UInt32)
        self.data += Hex.dump(self.formid)
        self.data += Integer.dump(self.timestamp, Integer.IntType.UInt16)
        self.data += Integer.dump(self.version_control_info, Integer.IntType.UInt16)
        self.data += Integer.dump(self.internal_version, Integer.IntType.UInt16)
        self.data += Integer.dump(self.unknown, Integer.IntType.UInt16)
        self.data += data

        return self.data
