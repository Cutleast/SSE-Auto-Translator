"""
Copyright (c) Cutleast
"""

import struct
from io import BufferedReader


class Integer:
    """
    Class for all types of signed and unsigned integers.
    """

    @staticmethod
    def _int(stream: BufferedReader, size: int):
        return int.from_bytes(stream.read(size), byteorder="little", signed=True)

    @staticmethod
    def uint(stream: BufferedReader, size: int):
        return int.from_bytes(stream.read(size), byteorder="little")

    @staticmethod
    def int8(stream: BufferedReader) -> int:
        """
        Integer of size 1.
        """

        return Integer._int(stream, 1)

    @staticmethod
    def int16(stream: BufferedReader) -> int:
        """
        Integer of size 2.
        """

        return Integer._int(stream, 2)

    @staticmethod
    def int32(stream: BufferedReader) -> int:
        """
        Integer of size 4.
        """

        return Integer._int(stream, 4)

    @staticmethod
    def int64(stream: BufferedReader) -> int:
        """
        Integer of size 8.
        """

        return Integer._int(stream, 8)

    @staticmethod
    def uint8(stream: BufferedReader) -> int:
        """
        Unsigned Integer of size 1.
        """

        return Integer.uint(stream, 1)

    @staticmethod
    def uint16(stream: BufferedReader) -> int:
        """
        Unsigned Integer of size 2.
        """

        return Integer.uint(stream, 2)

    @staticmethod
    def uint32(stream: BufferedReader) -> int:
        """
        Unsigned Integer of size 4.
        """

        return Integer.uint(stream, 4)

    @staticmethod
    def uint64(stream: BufferedReader) -> int:
        """
        Unsigned Integer of size 8.
        """

        return Integer.uint(stream, 8)

    @staticmethod
    def short(stream: BufferedReader) -> int:
        """
        Int16.
        """

        return Integer.int16(stream)

    @staticmethod
    def ushort(stream: BufferedReader) -> int:
        """
        Uint16.
        """

        return Integer.uint16(stream)

    @staticmethod
    def long(stream: BufferedReader) -> int:
        """
        Int32.
        """

        return Integer.int32(stream)

    @staticmethod
    def ulong(stream: BufferedReader) -> int:
        """
        Uint32.
        """

        return Integer.uint32(stream)


class Float:
    """
    Class for all types of floats.
    """

    @staticmethod
    def _float(stream: BufferedReader, size: int) -> float:
        return struct.unpack("f", stream.read(size))[0]

    @staticmethod
    def float32(stream: BufferedReader):
        return Float._float(stream, 4)

    @staticmethod
    def float64(stream: BufferedReader):
        return Float._float(stream, 4)

    @staticmethod
    def float(stream: BufferedReader):
        return Float.float32(stream)


class String:
    """
    Class for all types of chars and strings.
    """

    @staticmethod
    def decode(data: bytes) -> str:
        """
        Attempts to decode `data` with encodings in the following order:

        1. UTF-8
        2. Windows-1250 (cp1250)
        3. Windows-1252 (cp1252)
        4. Windows-1251 (cp1251)
        
        Raises UnicodeDecodeError if none of the encodings worked.
        """

        try:
            return data.decode("utf8")
        except UnicodeDecodeError:
            pass

        try:
            return data.decode("cp1250")
        except UnicodeDecodeError:
            pass
        
        try:
            return data.decode("cp1252")
        except UnicodeDecodeError:
            pass

        try:
            return data.decode("cp1251")
        except UnicodeDecodeError:
            pass

        return data.decode(errors="replace")

    @staticmethod
    def chars(stream: BufferedReader, size: int) -> bytes:
        """
        Chars of length `size`.
        """

        return stream.read(size)

    @staticmethod
    def char(stream: BufferedReader) -> bytes:
        """
        Single char.
        """

        return String.chars(stream, 1)

    @staticmethod
    def wchar(stream: BufferedReader) -> bytes:
        """
        Double char.
        """

        return String.chars(stream, 2)

    @staticmethod
    def string(stream: BufferedReader, size: int) -> str:
        """
        String of length `size`.
        """

        return String.decode(stream.read(size))

    @staticmethod
    def wstring(stream: BufferedReader) -> str:
        """
        String, precedented by length as uint8.
        """

        return String.string(stream, Integer.uint16(stream))

    @staticmethod
    def wzstring(stream: BufferedReader) -> str:
        """
        Null-terminated string, precedented by length as uint16.
        """

        return String.decode(String.chars(stream, Integer.uint16(stream))[:-1])

    @staticmethod
    def bzstring(stream: BufferedReader):
        """
        Null-terminated string, precedented by length as uint8.
        """

        return String.decode(String.chars(stream, Integer.uint8(stream))[:-1])

    @staticmethod
    def bstring(stream: BufferedReader):
        """
        BZString.
        """

        return String.bzstring(stream)

    @staticmethod
    def zstring(stream: BufferedReader) -> str:
        """
        Null-terminated string.
        """

        string = b""

        while (char := stream.read(1)) != b"\x00" and char:
            string += char

        return String.decode(string.removesuffix(b"\x00"))

    @staticmethod
    def lstring(stream: BufferedReader) -> str:
        """
        Null-terminated string, precedented by length as uint32.
        """

        length = Integer.uint32(stream)
        string = String.chars(stream, length)
        string = string.removesuffix(b"\x00")

        return String.decode(string)

    @staticmethod
    def list(stream: BufferedReader, count: int, sep=b"\x00"):
        """
        Returns a list of all strings seperated by <sep>
        until <count> is reached.
        """

        strings: list[str] = []

        while len(strings) < count:
            string = b""
            while (char := stream.read(1)) != sep:
                string += char

            strings.append(String.decode(string))

        return strings

    @staticmethod
    def stringId(stream: BufferedReader) -> int:
        return Integer.ulong(stream)


class Flags:
    """
    Class for all types of flags.
    """

    @staticmethod
    def flags(stream: BufferedReader, size: int, flags: dict[int, str]):
        # Convert the bytestring to an integer
        value = Integer._int(stream, size)

        parsed_flags: dict[str, bool] = {}

        for flag, description in flags.items():
            parsed_flags[description] = bool(value & flag)

        return parsed_flags


class Hex:
    """
    Class for all types of hexadecimal strings.
    """

    @staticmethod
    def hex(stream: BufferedReader, size: int):
        return hex(Integer.uint(stream, size)).removeprefix("0x").upper().zfill(8)
