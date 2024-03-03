"""
Copyright (c) Cutleast
"""

from io import BufferedReader, BytesIO
from . import utilities as utils
from .datatypes import Integer, String, Float


class Subrecord:
    """
    Contains parsed subrecord data.
    """

    data_stream: BufferedReader
    type: str = "Subrecord"

    def __init__(self, data_stream: BufferedReader, type: str = None):
        self.type = type if type else self.type
        self.data_stream = data_stream

    def __repr__(self):
        string = "\n\t\t{"

        for key, value in self.__dict__.items():
            if key != "data_stream" and key != "data":
                string += f"\n\t\t\t{key} = {value!r}"
            elif key == "data":
                string += f"\n\t\t\t{key} = {value[:64]!r}"

        string += "\n\t\t}"

        return string

    def __str__(self):
        return str(self.__dict__)

    def __len__(self):
        try:
            return self.size + 6
        except AttributeError:
            return 0

    def parse(self, flags: dict[str, bool]):
        self.type = String.string(self.data_stream, 4)
        self.size = Integer.uint16(self.data_stream)
        self.data = self.data_stream.read(self.size)


class HEDR(Subrecord):
    """
    Class for HEDR subrecord.
    """

    type = "HEDR"

    def parse(self, flags: dict[str, bool]):
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

    def parse(self, flags: dict[str, bool]):
        self.type = String.string(self.data_stream, 4)
        self.size = Integer.uint16(self.data_stream)
        self.editor_id = String.zstring(self.data_stream)


class StringSubrecord(Subrecord):
    """
    Class for string subrecords.
    """

    type = None
    index: int | None = None

    def parse(self, flags: dict[str, bool]):
        self.type = String.string(self.data_stream, 4)
        self.size = Integer.uint16(self.data_stream)
        self.data = utils.peek(self.data_stream, self.size)

        try:
            string = String.string(self.data_stream, self.size).removesuffix("\x00").strip()
            if utils.is_valid_string(string) or string.isnumeric():
                self.string = string
            else:
                self.string = None
        except UnicodeDecodeError:
            self.string = None


class MAST(Subrecord):
    """
    Class for MAST subrecord.
    """

    type = "MAST"

    def parse(self, flags: dict[str, bool]):
        super().parse(flags)

        stream = BytesIO(self.data)
        self.file = String.wzstring(stream)

        return self


class TIFC(Subrecord):
    """
    Class for TIFC subrecord.
    """

    type = "TIFC"

    def parse(self, flags: dict[str, bool]):
        super().parse(flags)

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
    # "EPF2": StringSubrecord,
    # "EPFD": StringSubrecord,
    "MAST": MAST,
    "TIFC": TIFC,
}
