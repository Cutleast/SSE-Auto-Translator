"""
Copyright (c) Cutleast
"""

from sse_plugin_interface.datatypes import Integer
from sse_plugin_interface.utilities import Stream

from .datatypes import String


class DirectoryEntry:
    """
    Contains parsed record data.
    """

    lstring: bool
    raw_data_offset: int
    string_id: int
    string: str

    def __init__(self, stream: Stream, lstring: bool, raw_data_offset: int) -> None:
        self.lstring = lstring
        self.raw_data_offset = raw_data_offset

        self.parse(stream)

    def parse(self, stream: Stream) -> None:
        self.string_id = Integer.parse(stream, Integer.IntType.UInt32)
        offset: int = Integer.parse(stream, Integer.IntType.UInt32)

        cur_offset: int = stream.tell()
        new_offset: int = self.raw_data_offset + offset

        stream.seek(new_offset)
        if self.lstring:
            self.string = String.lstring(stream)
        else:
            self.string = String.zstring(stream)

        stream.seek(cur_offset)
