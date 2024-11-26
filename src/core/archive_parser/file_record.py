"""
Copyright (c) Cutleast
"""

from dataclasses import dataclass
from io import BufferedReader

from .datatypes import Hash, Integer


@dataclass
class FileRecordBlock:
    """
    Class for file record block.
    """

    data_stream: BufferedReader

    def parse(self, count: int):
        self.name_length = Integer.int8(self.data_stream)
        self.name = self.data_stream.read(self.name_length)
        self.file_records = [FileRecord(self.data_stream).parse() for i in range(count)]

        return self


@dataclass
class FileRecord:
    """
    Class for file record.
    """

    data_stream: BufferedReader
    compressed = None

    def has_compression_flag(self) -> bool:
        # Mask for the 30th bit (0x40000000)
        mask = 0x40000000

        # Use bitwise AND to check if the 30th bit is set
        is_set = self.size & mask

        return is_set != 0

    def parse(self):
        self.name_hash = Hash.hash(self.data_stream)
        self.size = Integer.ulong(self.data_stream)
        self.offset = Integer.ulong(self.data_stream)

        return self
