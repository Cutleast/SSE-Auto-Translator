"""
Copyright (c) Cutleast
"""

from dataclasses import dataclass
from io import BufferedReader

from .datatypes import String


@dataclass
class FileNameBlock:
    """
    Class for file name block.
    """

    data_stream: BufferedReader

    def parse(self, count: int) -> "FileNameBlock":
        self.file_names = String.list(self.data_stream, count)

        return self
