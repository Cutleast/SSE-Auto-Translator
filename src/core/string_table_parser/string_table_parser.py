"""
Copyright (c) Cutleast
"""

from core.plugin_interface.datatypes import Stream
from core.utilities.path import Path

from .string_table import StringTable


class StringTableParser:
    """
    Class for string table parser.
    Used to parse string table files (.strings, .dlstrings, .ilstrings).
    """

    """
    String Table structure:
    Header
     -> uint32: Number of entries
     -> uint32: Size of string data after header and director
     -> Directory Entry
      -> uint32: String ID
      -> uint32: Offset
     -> uint8[dataSize]: Raw Data
      -> If .strings-File: zstring: Null-terminated string
      -> If .dlstrings/.ilstrings-File: uint32: Length of following string, incl. null-terminator
      -> If .dlstrings/.ilstrings-File: uint8[length]: Null-terminated string
    """

    file_path: Path
    parsed_data: StringTable

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def parse(self, stream: Stream) -> StringTable:
        """
        Parses the string table from the specified stream.

        Args:
            stream (Stream): Stream to parse.

        Returns:
            StringTable: Parsed string table.
        """

        lstring: bool = self.file_path.suffix.lower() in [".ilstrings", ".dlstrings"]
        self.parsed_data = StringTable(stream, lstring)

        return self.parsed_data
