"""
Copyright (c) Cutleast
"""

from dataclasses import dataclass
from io import BufferedReader

from .datatypes import Flags, Integer, String


@dataclass
class Header:
    """
    Class for archive header.
    """

    data_stream: BufferedReader

    ARCHIVE_FLAGS = {
        0x1: "Include Directory Names",
        0x2: "Include File Names",
        0x4: "Compressed Archive",
        0x8: "Retain Directory Names",
        0x10: "Retain File Names",
        0x20: "Retain File Name Offsets",
        0x40: "Xbox360 archive",
        0x80: "Retain Strings During Startup",
        0x100: "Embed File Names",
        0x200: "XMem Codec",
    }

    FILE_FLAGS = {
        0x1: "Meshes",
        0x2: "Textures",
        0x4: "Menus",
        0x8: "Sounds",
        0x10: "Voices",
        0x20: "Shaders",
        0x40: "Tress",
        0x80: "Fonts",
        0x100: "Miscellaneous",
    }

    def parse(self) -> "Header":
        self.file_id = String._char(self.data_stream, 4)
        self.version = Integer.ulong(self.data_stream)
        self.offset = Integer.ulong(self.data_stream)
        self.archive_flags = Flags.flags(self.data_stream, 4, self.ARCHIVE_FLAGS)
        self.folder_count = Integer.ulong(self.data_stream)
        self.file_count = Integer.ulong(self.data_stream)
        self.total_folder_name_length = Integer.ulong(self.data_stream)
        self.total_file_name_length = Integer.ulong(self.data_stream)
        self.file_flags = Flags.flags(self.data_stream, 2, self.FILE_FLAGS)
        self.padding = Integer.ushort(self.data_stream)

        return self
