"""
Copyright (c) Cutleast
"""

from sse_plugin_interface.utilities import Stream

from core.string_table_parser.utilities import get_stream_size

from .datatypes import Integer
from .directory_entry import DirectoryEntry


class StringTable:
    """
    Contains parsed string table data.
    """

    entries: list[DirectoryEntry]
    num_of_entries: int
    string_data_size: int
    raw_data_offset: int

    def __init__(self, stream: Stream, lstring: bool) -> None:
        self.parse(stream, lstring)

    def parse(self, stream: Stream, lstring: bool) -> None:
        self.num_of_entries = Integer.parse(stream, Integer.IntType.UInt32)
        self.string_data_size = Integer.parse(stream, Integer.IntType.UInt32)

        stream_size: int = get_stream_size(stream)
        self.raw_data_offset = stream_size - self.string_data_size

        self.entries = [
            DirectoryEntry(stream, lstring, self.raw_data_offset)
            for _ in range(self.num_of_entries)
        ]

    def extract_strings(self) -> dict[int, str]:
        """
        Extracts string ids and strings from the parsed string table.

        Returns:
            dict[int, str]: Dictionary with string ids and strings
        """

        strings: dict[int, str] = {
            entry.string_id: entry.string
            for entry in self.entries
            if entry.string.strip()
        }

        return strings
