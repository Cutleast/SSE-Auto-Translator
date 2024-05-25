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

    def int(stream: BufferedReader, size: int):
        return int.from_bytes(stream.read(size), byteorder="little", signed=True)

    def uint(stream: BufferedReader, size: int):
        return int.from_bytes(stream.read(size), byteorder="little")

    def int8(stream: BufferedReader):
        return Integer.int(stream, 1)

    def int16(stream: BufferedReader):
        return Integer.int(stream, 2)

    def int32(stream: BufferedReader):
        return Integer.int(stream, 4)

    def int64(stream: BufferedReader):
        return Integer.int(stream, 8)

    def uint8(stream: BufferedReader):
        return Integer.uint(stream, 1)

    def uint16(stream: BufferedReader):
        return Integer.uint(stream, 2)

    def uint32(stream: BufferedReader):
        return Integer.uint(stream, 4)

    def uint64(stream: BufferedReader):
        return Integer.uint(stream, 8)

    def short(stream: BufferedReader):
        return Integer.int16(stream)

    def ushort(stream: BufferedReader):
        return Integer.uint16(stream)

    def long(stream: BufferedReader):
        return Integer.int32(stream)

    def ulong(stream: BufferedReader):
        return Integer.uint32(stream)


class Float:
    """
    Class for all types of floats.
    """

    def _float(stream: BufferedReader, size: int):
        return struct.unpack("f", stream.read(size))[0]

    def float32(stream: BufferedReader):
        return Float._float(stream, 4)

    def float64(stream: BufferedReader):
        return Float._float(stream, 4)

    def float(stream: BufferedReader):
        return Float.float32(stream)


class String:
    """
    Class for all types of chars and strings.
    """

    def _char(stream: BufferedReader, size: int):
        return stream.read(size)

    def char(stream: BufferedReader):
        return String._char(stream, 1)

    def wchar(stream: BufferedReader):
        return String._char(stream, 2)

    def _string(stream: BufferedReader, size: int):
        return stream.read(size).decode()

    def wstring(stream: BufferedReader):
        return String._string(stream, Integer.uint16(stream))

    def bzstring(stream: BufferedReader):
        return String._char(stream, Integer.uint8(stream))

    def bstring(stream: BufferedReader):
        return String.bzstring(stream)

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

            strings.append(string.decode())

        return strings


class Flags:
    """
    Class for all types of flags.
    """

    def flags(stream: BufferedReader, size: int, flags: dict[int, str]):
        # Convert the bytestring to an integer
        value = Integer.int(stream, size)

        parsed_flags = {}

        for flag, description in flags.items():
            parsed_flags[description] = bool(value & flag)

        return parsed_flags


class Hex:
    """
    Class for all types of hexadecimal strings.
    """

    def hex(stream: BufferedReader, size: int):
        return stream.read(size).hex()


class Hash:
    """
    Class for all types of hashes.
    """

    def hash(stream: BufferedReader):
        return Integer.uint64(stream)

    def calc_hash(filename: str):
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
            chars[-1]
            | (0, chars[-2])[len(chars) > 2] << 8
            | len(chars) << 16
            | chars[0] << 24
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
        for char in chars[1:-2]:  # --Slice of the chars array
            hash2 = ((hash2 * 0x1003F) + char) & uintMask
        for char in map(ord, ext):
            hash3 = ((hash3 * 0x1003F) + char) & uintMask
        hash2 = (hash2 + hash3) & uintMask
        # --Done
        return (hash2 << 32) + hash1  # --Return as uint64
