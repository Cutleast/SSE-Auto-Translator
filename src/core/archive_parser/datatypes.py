"""
Copyright (c) Cutleast
"""

import os
import struct
from io import BufferedReader


class Integer:
    """
    Class for all types of signed and unsigned integers.
    """

    @staticmethod
    def _int(stream: BufferedReader, size: int) -> int:
        return int.from_bytes(stream.read(size), byteorder="little", signed=True)

    @staticmethod
    def uint(stream: BufferedReader, size: int) -> int:
        return int.from_bytes(stream.read(size), byteorder="little")

    @staticmethod
    def int8(stream: BufferedReader) -> int:
        return Integer._int(stream, 1)

    @staticmethod
    def int16(stream: BufferedReader) -> int:
        return Integer._int(stream, 2)

    @staticmethod
    def int32(stream: BufferedReader) -> int:
        return Integer._int(stream, 4)

    @staticmethod
    def int64(stream: BufferedReader) -> int:
        return Integer._int(stream, 8)

    @staticmethod
    def uint8(stream: BufferedReader) -> int:
        return Integer.uint(stream, 1)

    @staticmethod
    def uint16(stream: BufferedReader) -> int:
        return Integer.uint(stream, 2)

    @staticmethod
    def uint32(stream: BufferedReader) -> int:
        return Integer.uint(stream, 4)

    @staticmethod
    def uint64(stream: BufferedReader) -> int:
        return Integer.uint(stream, 8)

    @staticmethod
    def short(stream: BufferedReader) -> int:
        return Integer.int16(stream)

    @staticmethod
    def ushort(stream: BufferedReader) -> int:
        return Integer.uint16(stream)

    @staticmethod
    def long(stream: BufferedReader) -> int:
        return Integer.int32(stream)

    @staticmethod
    def ulong(stream: BufferedReader) -> int:
        return Integer.uint32(stream)


class Float:
    """
    Class for all types of floats.
    """

    @staticmethod
    def _float(stream: BufferedReader, size: int) -> float:
        value: float = struct.unpack("f", stream.read(size))[0]
        return value

    @staticmethod
    def float32(stream: BufferedReader) -> float:
        return Float._float(stream, 4)

    @staticmethod
    def float64(stream: BufferedReader) -> float:
        return Float._float(stream, 4)

    @staticmethod
    def float(stream: BufferedReader) -> float:
        return Float.float32(stream)


class String:
    """
    Class for all types of chars and strings.
    """

    @staticmethod
    def _char(stream: BufferedReader, size: int) -> bytes:
        return stream.read(size)

    @staticmethod
    def char(stream: BufferedReader) -> bytes:
        return String._char(stream, 1)

    @staticmethod
    def wchar(stream: BufferedReader) -> bytes:
        return String._char(stream, 2)

    @staticmethod
    def _string(stream: BufferedReader, size: int) -> str:
        return stream.read(size).decode()

    @staticmethod
    def wstring(stream: BufferedReader) -> str:
        return String._string(stream, Integer.uint16(stream))

    @staticmethod
    def bzstring(stream: BufferedReader) -> bytes:
        return String._char(stream, Integer.uint8(stream))

    @staticmethod
    def bstring(stream: BufferedReader) -> bytes:
        return String.bzstring(stream)

    @staticmethod
    def list(stream: BufferedReader, count: int, sep: bytes = b"\x00") -> list[str]:
        """
        Returns a list of all strings seperated by <sep>
        until <count> is reached.
        """

        strings: list[str] = []

        while len(strings) < count:
            string = b""
            while (char := stream.read(1)) != sep:
                string += char

            strings.append(string.decode("cp1252"))

        return strings


class Flags:
    """
    Class for all types of flags.
    """

    @staticmethod
    def flags(
        stream: BufferedReader, size: int, flags: dict[int, str]
    ) -> dict[str, bool]:
        # Convert the bytestring to an integer
        value: int = Integer._int(stream, size)

        parsed_flags: dict[str, bool] = {}

        for flag, description in flags.items():
            parsed_flags[description] = bool(value & flag)

        return parsed_flags


class Hex:
    """
    Class for all types of hexadecimal strings.
    """

    @staticmethod
    def hex(stream: BufferedReader, size: int) -> str:
        return stream.read(size).hex()


class Hash:
    """
    Class for all types of hashes.
    """

    @staticmethod
    def hash(stream: BufferedReader) -> int:
        return Integer.uint64(stream)

    @staticmethod
    def calc_hash(filename: str) -> int:
        """
        Returns tes4's two hash values for filename.
        Based on TimeSlips code with cleanup and pythonization.

        This function is from here:
        https://en.uesp.net/wiki/Oblivion_Mod:Hash_Calculation#Python
        """

        root, ext = os.path.splitext(
            filename.lower()
        )  # --"bob.dds" >> root = "bob", ext = ".dds"
        # --Hash1
        chars = map(ord, root)  # --'bob' >> chars = [98,111,98]
        hash1 = (
            chars[-1]  # type: ignore
            | (0, chars[-2])[len(chars) > 2] << 8  # type: ignore
            | len(chars) << 16  # type: ignore
            | chars[0] << 24  # type: ignore
        )
        # --(a,b)[test] is similar to test?a:b in C. (Except that evaluation is not shortcut.)
        if ext == ".kf":
            hash1 |= 0x80
        elif ext == ".nif":
            hash1 |= 0x8000
        elif ext == ".dds":
            hash1 |= 0x8080
        elif ext == ".wav":
            hash1 |= 0x80000000
        # --Hash2
        # --Python integers have no upper limit. Use uintMask to restrict these to 32 bits.
        uintMask, hash2, hash3 = 0xFFFFFFFF, 0, 0
        for char in chars[1:-2]:  # type: ignore[index]  # --Slice of the chars array
            hash2 = ((hash2 * 0x1003F) + char) & uintMask
        for char in map(ord, ext):
            hash3 = ((hash3 * 0x1003F) + char) & uintMask
        hash2 = (hash2 + hash3) & uintMask
        # --Done
        return (  # type: ignore[no-any-return]
            hash2 << 32
        ) + hash1  # --Return as uint64
