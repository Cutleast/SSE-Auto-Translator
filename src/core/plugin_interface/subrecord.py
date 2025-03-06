"""
Copyright (c) Cutleast
"""

import logging
from io import BytesIO
from typing import Optional, override

from .datatypes import Float, Hex, Integer, RawString, Stream
from .flags import RecordFlags
from .utilities import prettyprint_object


class Subrecord:
    """
    Contains parsed subrecord data.
    """

    type: str
    size: int
    data: bytes
    index: Optional[int] = None

    log = logging.getLogger("PluginParser.Subrecord")

    def __init__(self, type: Optional[str] = None):
        if type is not None:
            self.type = type

    @override
    def __repr__(self) -> str:
        return prettyprint_object(self)

    @override
    def __str__(self) -> str:
        return str(self.__dict__)

    def __len__(self) -> int:
        return len(self.dump())

    def parse(self, stream: Stream, header_flags: RecordFlags) -> None:
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

    @override
    def parse(self, stream: Stream, header_flags: RecordFlags) -> None:
        super().parse(stream, header_flags)

        stream = BytesIO(self.data)

        self.version = Float.parse(stream, Float.FloatType.Float32)
        self.records_num = Integer.parse(stream, Integer.IntType.UInt32)
        self.next_object_id = Hex.parse(stream)

    @override
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

    @override
    def parse(self, stream: Stream, header_flags: RecordFlags) -> None:
        super().parse(stream, header_flags)

        self.editor_id = RawString.parse(self.data, RawString.StrType.ZString)  # type: ignore

    @override
    def dump(self) -> bytes:
        self.data = RawString.dump(self.editor_id, RawString.StrType.ZString)

        return super().dump()


class StringSubrecord(Subrecord):
    """
    Class for string subrecords.
    """

    string: RawString | int

    log = logging.getLogger("PluginParser.StringSubrecord")

    @override
    def parse(self, stream: Stream, header_flags: RecordFlags) -> None:
        super().parse(stream, header_flags)

        if RecordFlags.Localized in header_flags:
            self.string = Integer.parse(self.data, Integer.IntType.UInt32)

        else:
            self.string = RawString.parse(  # type: ignore
                self.data, RawString.StrType.ZString, self.size
            )

    def set_string(self, string: str) -> None:
        if isinstance(self.string, int):
            raise ValueError("Cannot replace string in a localized record!")

        encoding = self.string.encoding

        self.string = RawString.from_str(string, encoding)

    @override
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

    file: RawString

    @override
    def parse(self, stream: Stream, header_flags: RecordFlags) -> None:
        super().parse(stream, header_flags)

        self.file = RawString.parse(self.data, RawString.StrType.ZString)  # type: ignore

    @override
    def dump(self) -> bytes:
        self.data = RawString.dump(self.file, RawString.StrType.ZString)

        return super().dump()


class XXXX(Subrecord):
    """
    Class for special XXXX subrecord.
    """

    field_size: int

    @override
    def parse(self, stream: Stream, header_flags: RecordFlags) -> None:
        super().parse(stream, header_flags)

        self.field_size = Integer.parse(self.data, (self.size, False))
        # Add header and data of following subrecord to this
        self.data = stream.read(self.field_size + 6)

    @override
    def dump(self) -> bytes:
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

    @override
    def parse(self, stream: Stream, header_flags: RecordFlags) -> None:
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

    @override
    def dump(self) -> bytes:
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

    @override
    def parse(self, stream: Stream, header_flags: RecordFlags) -> None:
        super().parse(stream, header_flags)

        self.index = Integer.parse(self.data, Integer.IntType.Int16)  # type: ignore

    @override
    def dump(self) -> bytes:
        self.data = Integer.dump(self.index, Integer.IntType.Int16)

        return super().dump()


class EPFT(Subrecord):
    """
    Class for EPFT subrecord.
    """

    perk_type: int

    @override
    def parse(self, stream: Stream, header_flags: RecordFlags) -> None:
        super().parse(stream, header_flags)

        self.perk_type = Integer.parse(self.data, Integer.IntType.UInt8)

    @override
    def dump(self) -> bytes:
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
