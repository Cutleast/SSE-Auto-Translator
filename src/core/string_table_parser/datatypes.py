"""
Copyright (c) Cutleast
"""

from core.plugin_interface.datatypes import Integer, RawString
from core.plugin_interface.utilities import Stream


class String:
    """
    Class for all types of chars and strings.
    """

    @staticmethod
    def zstring(stream: Stream) -> str:
        """
        Null-terminated string.
        """

        string = b""

        while (char := stream.read(1)) != b"\x00":
            string += char

        for encoding in RawString.SUPPORTED_ENCODINGS:
            try:
                return string.decode(encoding)
            except UnicodeDecodeError:
                pass

        return string.decode("utf8", errors="ignore")

    @staticmethod
    def lstring(stream: Stream) -> str:
        """
        Null-terminated string, precedented by length as uint32.
        """

        length: int = Integer.parse(stream, Integer.IntType.UInt32)
        string: bytes = stream.read(length).removesuffix(b"\x00")

        for encoding in RawString.SUPPORTED_ENCODINGS:
            try:
                return string.decode(encoding)
            except UnicodeDecodeError:
                pass

        return string.decode("utf8", errors="ignore")
