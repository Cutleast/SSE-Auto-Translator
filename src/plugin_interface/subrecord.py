"""
Copyright (c) Cutleast
"""

import logging
from io import BufferedReader, BytesIO

from .datatypes import Float, Hex, Integer, RawString
from .flags import RecordFlags
from .utilities import prettyprint_object


class Subrecord:
    """
    Contains parsed subrecord data.
    """

    type: str
    size: int
    data: bytes

    log = logging.getLogger("PluginParser.Subrecord")

    def __init__(
        self,
        type: str = None,
    ):
        self.type = type

    def __repr__(self) -> str:
        return prettyprint_object(self)

    def __str__(self):
        return str(self.__dict__)

    def __len__(self):
        return len(self.dump())

    def parse(self, stream: BufferedReader, header_flags: RecordFlags):
        self.type = stream.read(4).decode()
        self.size = Integer.parse(stream, Integer.IntType.UInt16)
        self.data = stream.read(self.size)

    def dump(self) -> bytes:
        self.size = len(self.data)

        data = b""
        data += self.type.encode()
        data += Integer.dump(self.size, Integer.IntType.UInt16)
        data += self.data

        return data


class HEDR(Subrecord):
    """
    Class for HEDR subrecord.
    """

    version: float
    records_num: int
    next_object_id: str

    def parse(self, stream: BufferedReader, header_flags: RecordFlags):
        super().parse(stream, header_flags)

        stream = BytesIO(self.data)

        self.version = Float.parse(stream, Float.FloatType.Float32)
        self.records_num = Integer.parse(stream, Integer.IntType.UInt32)
        self.next_object_id = Hex.parse(stream)

    def dump(self) -> bytes:
        self.data = b""

        self.data += Float.dump(self.version, Float.FloatType.Float32)
        self.data += Integer.dump(self.records_num, Integer.IntType.UInt32)
        self.data += Hex.dump(self.next_object_id)

        return super().dump()


class EDID(Subrecord):
    """
    Class for EDID subrecord.
    """

    editor_id: RawString

    def parse(self, stream: BufferedReader, header_flags: RecordFlags):
        super().parse(stream, header_flags)

        self.editor_id = RawString.parse(self.data, RawString.StrType.ZString)

    def dump(self) -> bytes:
        self.data = RawString.dump(self.editor_id, RawString.StrType.ZString)

        return super().dump()


class StringSubrecord(Subrecord):
    """
    Class for string subrecords.
    """

    string: RawString | int
    index: int = None

    log = logging.getLogger("PluginParser.StringSubrecord")

    def parse(self, stream: BufferedReader, header_flags: RecordFlags):
        super().parse(stream, header_flags)

        if RecordFlags.Localized in header_flags:
            self.string = Integer.parse(self.data, Integer.IntType.UInt32)

        else:
            self.string = RawString.parse(
                self.data, RawString.StrType.ZString, self.size
            )

    def set_string(self, string: str):
        encoding = self.string.encoding

        self.string = RawString.from_str(string, encoding)

    def dump(self) -> bytes:
        if isinstance(self.string, int):
            self.data = Integer.dump(self.string, Integer.IntType.UInt32)

        else:
            self.data = RawString.dump(self.string, RawString.StrType.ZString)

        return super().dump()


class MAST(Subrecord):
    """
    Class for MAST subrecord.
    """

    file: str

    def parse(self, stream: BufferedReader, header_flags: RecordFlags):
        super().parse(stream, header_flags)

        self.file = RawString.parse(self.data, RawString.StrType.ZString)

    def dump(self) -> bytes:
        self.data = RawString.dump(self.file, RawString.StrType.ZString)

        return super().dump()


class XXXX(Subrecord):
    """
    Class for special XXXX subrecord.
    """

    field_size: int

    def parse(self, stream: BufferedReader, header_flags: RecordFlags):
        super().parse(stream, header_flags)

        self.field_size = Integer.parse(self.data, (self.size, False))
        # Add header and data of following subrecord to this
        self.data = stream.read(self.field_size + 6)

    def dump(self):
        data = b""

        data += self.type.encode()
        data += Integer.dump(self.size, Integer.IntType.UInt16)
        data += Integer.dump(self.field_size, (self.size, False))
        data += self.data

        return data


class TRDT(Subrecord):
    """
    Class for TRDT subrecord.
    """

    emotion_type: int
    emotion_value: int
    unknown1: int
    response_id: int
    junk1: bytes
    sound_file: str
    use_emo_anim: int
    junk2: bytes

    def parse(self, stream: BufferedReader, header_flags: RecordFlags):
        super().parse(stream, header_flags)

        stream = BytesIO(self.data)

        self.emotion_type = Integer.parse(stream, Integer.IntType.UInt32)
        self.emotion_value = Integer.parse(stream, Integer.IntType.UInt32)
        self.unknown1 = Integer.parse(stream, Integer.IntType.Int32)
        self.response_id = Integer.parse(stream, Integer.IntType.UInt8)
        self.junk1 = stream.read(3)
        self.sound_file = Hex.parse(stream)
        self.use_emo_anim = Integer.parse(stream, Integer.IntType.UInt8)
        self.junk2 = stream.read(3)

    def dump(self):
        self.data = b""

        self.data += Integer.dump(self.emotion_type, Integer.IntType.UInt32)
        self.data += Integer.dump(self.emotion_value, Integer.IntType.UInt32)
        self.data += Integer.dump(self.unknown1, Integer.IntType.Int32)
        self.data += Integer.dump(self.response_id, Integer.IntType.UInt8)
        self.data += self.junk1
        self.data += Hex.dump(self.sound_file)
        self.data += Integer.dump(self.use_emo_anim, Integer.IntType.UInt8)
        self.data += self.junk2

        return super().dump()


class QOBJ(Subrecord):
    """
    Class for QOBJ subrecord.
    """

    index: int

    def parse(self, stream: BufferedReader, header_flags: RecordFlags):
        super().parse(stream, header_flags)

        self.index = Integer.parse(self.data, Integer.IntType.Int16)

    def dump(self):
        self.data = Integer.dump(self.index, Integer.IntType.Int16)

        return super().dump()


class EPFT(Subrecord):
    """
    Class for EPFT subrecord.
    """

    perk_type: int

    def parse(self, stream: BufferedReader, header_flags: RecordFlags):
        super().parse(stream, header_flags)

        self.perk_type = Integer.parse(self.data, Integer.IntType.UInt8)

    def dump(self):
        self.data = Integer.dump(self.perk_type, Integer.IntType.UInt8)

        return super().dump()


SUBRECORD_MAP: dict[str, type[Subrecord]] = {
    "HEDR": HEDR,
    "EDID": EDID,
    "MAST": MAST,
    "TRDT": TRDT,
    "QOBJ": QOBJ,
    "EPFT": EPFT,
    "XXXX": XXXX,
}
