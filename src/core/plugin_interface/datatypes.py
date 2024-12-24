"""
Copyright (c) Cutleast
"""

from __future__ import annotations

import enum
import struct
from enum import Enum, auto
from typing import Optional, Self

from .utilities import Stream, get_stream, read_data


class Integer:
    """
    Class for all types of signed and unsigned integers.
    """

    class IntType(Enum):
        UInt8 = (1, False)
        """Unsigned Integer of size 1."""

        UInt16 = UShort = (2, False)
        """Unsigned Integer of size 2."""

        UInt32 = ULong = (4, False)
        """Unsigned Integer of size 4."""

        UInt64 = (8, False)
        """Unsigned Integer of size 8."""

        Int8 = (1, True)
        """Signed Integer of Size 1."""

        Int16 = Short = (2, True)
        """Signed Integer of Size 2."""

        Int32 = Long = (4, True)
        """Signed Integer of Size 4."""

        Int64 = (8, True)
        """Signed Integer of Size 8."""

    @staticmethod
    def parse(data: Stream | bytes, type: IntType | tuple[int, bool]) -> int:
        if isinstance(type, Integer.IntType):
            size, signed = type.value
        else:
            size, signed = type

        return int.from_bytes(
            get_stream(data).read(size), byteorder="little", signed=signed
        )

    @staticmethod
    def dump(value: int, type: IntType | tuple[int, bool]) -> bytes:
        if isinstance(type, Integer.IntType):
            size, signed = type.value
        else:
            size, signed = type

        return value.to_bytes(size, byteorder="little", signed=signed)


class Float:
    """
    Class for all types of floats.
    """

    class FloatType(Enum):
        Float32 = (4, "f")
        """Float of Size 4."""

        Float64 = (8, "d")
        """Float of Size 8."""

        Float = (4, "f")
        """Alias for Float32."""

        Double = (8, "d")
        """Alias for Float64."""

    @staticmethod
    def parse(data: Stream | bytes, type: FloatType) -> float:
        size, format = type.value

        value: float = struct.unpack(format, get_stream(data).read(size))[0]
        return value

    @staticmethod
    def dump(value: float, type: FloatType) -> bytes:
        size, format = type.value

        return struct.pack(format, value)


class RawString(str):
    """
    Class for all types of chars and strings.
    """

    SUPPORTED_ENCODINGS = ["utf8", "cp1250", "cp1252", "cp1251"]

    class StrType(Enum):
        Char = auto()
        """8-bit character."""

        WChar = auto()
        """16-bit character."""

        BZString = auto()
        """Null-terminated string prefixed by UInt8."""

        BString = auto()
        """Not-terminated string prefixed by UInt8."""

        WString = auto()
        """Not-terminated string prefixed by UInt16."""

        WZString = auto()
        """Null-terminated string prefixed by UInt16."""

        ZString = auto()
        """Null-terminated string."""

        String = auto()
        """Not-terminated string."""

        List = auto()
        """List of strings separated by `\\x00`."""

    encoding: str

    @staticmethod
    def from_str(string: str, encoding: str) -> RawString:
        """
        Converts `string` to a RawString object.
        """

        raw = RawString(string)
        raw.encoding = encoding

        return raw

    @staticmethod
    def decode(data: bytes) -> RawString:
        """
        Tries to decode `data` using all supported encodings.
        """

        for encoding in RawString.SUPPORTED_ENCODINGS:
            try:
                string = RawString(data.decode(encoding))
                string.encoding = encoding
                return string
            except UnicodeDecodeError:
                pass
        else:
            string = RawString(data.decode(encoding, errors="replace"))
            string.encoding = "utf8"  # Fallback to UTF-8 if encoding is unknown
            return string

    @staticmethod
    def encode(string: RawString) -> bytes:
        """
        Tries to encode `string` using all supported encodings.
        """

        for encoding in RawString.SUPPORTED_ENCODINGS:
            try:
                data = str(string).encode(encoding)
                string.encoding = encoding
                return data
            except UnicodeEncodeError:
                pass
        else:
            data = str(string).encode("utf8", errors="replace")
            string.encoding = "utf8"  # Fallback to UTF-8 if encoding is unknown
            return data

    @staticmethod
    def parse(
        data: Stream | bytes, type: StrType, size: Optional[int] = None
    ) -> bytes | RawString | list[RawString]:
        stream: Stream = get_stream(data)

        match type:
            case type.Char:
                return read_data(stream, 1)

            case type.WChar:
                return read_data(stream, 2)

            case type.BZString | type.BString:
                size = Integer.parse(stream, Integer.IntType.UInt8)
                data = read_data(stream, size).strip(b"\x00")
                return RawString.decode(data)

            case type.WString | type.WZString:
                size = Integer.parse(stream, Integer.IntType.Int16)
                data = read_data(stream, size).strip(b"\x00")
                return RawString.decode(data)

            case type.ZString:
                data = b""
                while (char := stream.read(1)) != b"\x00" and char:
                    data += char

                return RawString.decode(data)

            case type.String:
                data = read_data(stream, size)
                return RawString.decode(data)

            case type.List:
                strings: list[RawString] = []

                while len(strings) < size:
                    string = b""
                    while (char := stream.read(1)) != b"\x00" and char:
                        string += char

                    if string:
                        strings.append(RawString.decode(string))

                return strings

    @staticmethod
    def dump(value: "list[RawString]|RawString", type: StrType) -> bytes:
        match type:
            case type.Char | type.WChar | type.String:
                if isinstance(value, list):
                    raise ValueError("Wrong type for list of strings!")
                return RawString.encode(value)

            case type.BString:
                text = RawString.encode(value)
                size = Integer.dump(len(text), Integer.IntType.UInt8)
                return size + text

            case type.BZString:
                text = RawString.encode(value) + b"\x00"
                size = Integer.dump(len(text), Integer.IntType.UInt8)
                return size + text

            case type.WString:
                text = RawString.encode(value)
                size = Integer.dump(len(text), Integer.IntType.UInt16)
                return size + text

            case type.WZString:
                text = RawString.encode(value) + b"\x00"
                size = Integer.dump(len(text), Integer.IntType.UInt16)
                return size + text

            case type.ZString:
                return RawString.encode(value) + b"\x00"

            case type.List:
                data = b"\x00".join(RawString.encode(v) for v in value) + b"\x00"

                return data


class Flags(enum.IntFlag):
    """
    Class for all types of flags.
    """

    @classmethod
    def parse(cls, data: Stream | bytes, type: Integer.IntType) -> Self:
        value = Integer.parse(data, type)

        flag = cls(value)

        return flag

    def dump(self, type: Integer.IntType) -> bytes:
        return Integer.dump(self.value, type)


class Hex:
    """
    Class for all types of hexadecimal strings.

    `type` defaults to FormID-suitable integers.
    """

    @staticmethod
    def parse(
        data: Stream | bytes, type: Integer.IntType = Integer.IntType.ULong
    ) -> str:
        number = Integer.parse(data, type)

        return hex(number).removeprefix("0x").upper().zfill(8)

    @staticmethod
    def dump(value: str, type: Integer.IntType = Integer.IntType.ULong) -> bytes:
        number = int(value, base=16)

        return Integer.dump(number, type)
