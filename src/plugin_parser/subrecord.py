"""
Copyright (c) Cutleast
"""

import logging
from io import BufferedReader, BytesIO

from . import utilities as utils
from .datatypes import Float, Integer, String


class Subrecord:
    """
    Contains parsed subrecord data.
    """

    data_stream: BufferedReader = None
    header_flags: dict[str, bool] = None
    type: str = "Subrecord"

    log = logging.getLogger("PluginParser.Subrecord")

    def __init__(
        self,
        data_stream: BufferedReader,
        header_flags: dict[str, bool],
        type: str = None,
    ):
        self.data_stream = data_stream
        self.header_flags = header_flags
        self.type = type if type else self.type

    def __repr__(self) -> str:
        import pprint

        text = "\n" + pprint.pformat(self.__dict__, indent=4, sort_dicts=False)
        lines: list[str] = []
        for line in text.splitlines():
            line = " " * 8 + line
            lines.append(line)
        return "\n".join(lines)

    def __str__(self):
        return str(self.__dict__)

    def __len__(self):
        try:
            return self.size + 6
        except AttributeError:
            return 0

    def parse(self):
        self.type = String.string(self.data_stream, 4)
        self.size = Integer.uint16(self.data_stream)
        self.data = self.data_stream.read(self.size)


class HEDR(Subrecord):
    """
    Class for HEDR subrecord.
    """

    type = "HEDR"

    def parse(self):
        self.type = String.string(self.data_stream, 4)
        self.size = Integer.uint16(self.data_stream)
        self.version = round(Float.float32(self.data_stream), 2)
        self.records_num = Integer.uint32(self.data_stream)
        self.next_object_id = Integer.uint32(self.data_stream)


class EDID(Subrecord):
    """
    Class for EDID subrecord.
    """

    type = "EDID"

    def parse(self):
        self.type = String.string(self.data_stream, 4)
        self.size = Integer.uint16(self.data_stream)
        self.editor_id = String.zstring(self.data_stream)


class StringSubrecord(Subrecord):
    """
    Class for string subrecords.
    """

    type = None
    index: int | None = None
    string: str | int = None

    log = logging.getLogger("PluginParser.StringSubrecord")

    def parse(self):
        self.type = String.string(self.data_stream, 4)
        self.size = Integer.uint16(self.data_stream)
        self.data = utils.peek(self.data_stream, self.size)

        if self.header_flags["Localized"]:
            self.string = String.stringId(self.data_stream)

        else:
            try:
                string = (
                    String.string(self.data_stream, self.size)
                    .removesuffix("\x00")
                    .strip()
                )
                if utils.is_valid_string(string):
                    self.string = string
                else:
                    self.string = None
            except UnicodeDecodeError:
                self.log.warning(f"Failed to decode String data: {self.data!r}")
                self.string = None
                raise


class MAST(Subrecord):
    """
    Class for MAST subrecord.
    """

    type = "MAST"

    def parse(self):
        super().parse()

        stream = BytesIO(self.data)
        self.file = String.wzstring(stream)

        return self


class TIFC(Subrecord):
    """
    Class for TIFC subrecord.
    """

    type = "TIFC"

    def parse(self):
        super().parse()

        stream = BytesIO(self.data)
        self.count = Integer.uint32(stream)

        return self


SUBRECORD_MAPPING: dict[str, Subrecord] = {
    "HEDR": HEDR,
    "EDID": EDID,
    "FULL": StringSubrecord,
    "DESC": StringSubrecord,
    "NAM1": StringSubrecord,
    "NNAM": StringSubrecord,
    "CNAM": StringSubrecord,
    "TNAM": StringSubrecord,
    "RNAM": StringSubrecord,
    "SHRT": StringSubrecord,
    "DNAM": StringSubrecord,
    "ITXT": StringSubrecord,
    "EPF2": StringSubrecord,
    "EPFD": StringSubrecord,
    "MAST": MAST,
    "TIFC": TIFC,
}
