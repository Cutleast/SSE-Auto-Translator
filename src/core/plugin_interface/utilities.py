"""
Copyright (c) Cutleast
"""

from io import BufferedReader, BytesIO
from pathlib import Path
from typing import TypeAlias

import jstyleson as json
from cutleast_core_lib.core.utilities.exe_info import get_current_path

Stream: TypeAlias = BufferedReader | BytesIO
"""
Type alias for `BufferedReader` and `BytesIO`.
"""

# Load file that defines which records contain subrecords that are strings
whitelist_path: Path = get_current_path() / "res" / "string_records.json"
with whitelist_path.open() as whitelist_file:
    STRING_RECORDS: dict[str, list[str]] = json.load(whitelist_file)


def peek(stream: Stream, length: int) -> bytes:
    """
    Peeks into stream and returns data.
    """

    data = stream.read(length)

    stream.seek(-length, 1)

    return data


CHAR_WHITELIST = [
    "\n",
    "\r",
    "\t",
    "\u200b",
    "\xa0",
    "\u3000",
]


STRING_BLACKLIST = [
    "<p>",
]


STRING_WHITELIST = [
    "WoollyRhino",
    "CuSith",
]


def get_checksum(number: int) -> int:
    """
    Returns horizontal checksum of `number` (sum of all digits).
    """

    number = abs(number)

    return sum(int(digit) for digit in str(number))


def is_camel_case(text: str) -> bool:
    """
    Checks if `text` is camel case without spaces.
    """

    if len(text) < 3:
        return False

    return (
        any(char.isupper() and char.isalpha() for char in text[2:])
        and not text.isupper()
        and text.isalnum()
    )


def is_snake_case(text: str) -> bool:
    """
    Checks if `text` is snake case without spaces.
    """

    return " " not in text and "_" in text


def is_valid_string(text: str) -> bool:
    """
    Checks if <text> is a valid string.
    """

    if not text.strip() or text in STRING_BLACKLIST:
        return False

    if text in STRING_WHITELIST or "<Alias" in text:
        return True

    if is_camel_case(text) or is_snake_case(text):
        return False

    return all(char.isprintable() or char in CHAR_WHITELIST for char in text)


def get_stream(data: BytesIO | BufferedReader | bytes) -> Stream:
    if isinstance(data, bytes):
        return BytesIO(data)

    return data


def read_data(data: Stream | bytes, size: int) -> bytes:
    """
    Returns `size` bytes from `data`.
    """

    if isinstance(data, bytes):
        return data[:size]
    else:
        return data.read(size)


def indent_text(text: str, indent: int = 4) -> str:
    lines: list[str] = []

    for line in text.splitlines():
        if line.strip():
            lines.append(" " * indent + line)

    if text.endswith("\n"):
        return "\n".join(lines) + "\n"
    else:
        return "\n".join(lines)


def prettyprint_object(obj: object) -> str:
    text = "\r{\n"
    text += f"    class = {type(obj).__name__}\n"

    for key, val in obj.__dict__.items():
        if isinstance(val, list):
            if len(val) == 0:
                text += indent_text(f"{key}: list = []\n")
            else:
                text += indent_text(f"{key}: list = [\n")

                for item in val:
                    text += indent_text(prettyprint_object(item), 8) + ",\n"

                text += "    ]\n"
        elif isinstance(val, str) or isinstance(val, bytes):
            text += indent_text(f"{key}: {type(val).__name__} = {val[:20]!r}\n")
        else:
            text += indent_text(f"{key}: {type(val).__name__} = {val!r}\n")

    text += "}"

    return text
