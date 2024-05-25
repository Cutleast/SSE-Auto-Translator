"""
Copyright (c) Cutleast
"""

from dataclasses import dataclass
from io import BufferedReader

from .datatypes import Hash, Integer


@dataclass
class FolderRecord:
    """
    Class for folder records.
    """

    data_stream: BufferedReader

    def parse(self):
        self.name_hash = Hash.hash(self.data_stream)
        self.count = Integer.ulong(self.data_stream)
        self.padding = Integer.ulong(self.data_stream)
        self.offset = Integer.ulong(self.data_stream)
        self.padding2 = Integer.ulong(self.data_stream)

        return self
