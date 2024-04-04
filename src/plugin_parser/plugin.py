"""
Copyright (c) Cutleast
"""

from dataclasses import dataclass
from io import BufferedReader

from . import utilities as utils
from .group import Group
from .record import Record


@dataclass
class Plugin:
    """
    Contains parsed plugin data.
    """

    data_stream: BufferedReader
    header: Record = None
    groups: list[Group] = None

    def __repr__(self) -> str:
        import pprint

        text = "\n" + pprint.pformat(self.__dict__, indent=4, sort_dicts=False)
        lines: list[str] = []
        for line in text.splitlines():
            lines.append(line)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.__repr__()

    def parse(self):
        self.groups = []

        self.header = Record(self.data_stream, header_flags={})

        while utils.peek(self.data_stream, 1):
            self.groups.append(Group(self.data_stream, self.header.flags))

        return self
