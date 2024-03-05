"""
Copyright (c) Cutleast
"""

from io import BufferedReader
from pathlib import Path

import jstyleson as json

# Whitelist for record types that are known to work
# And that contain strings that are visible in-game
whitelist_path = Path(".") / "data" / "app" / "parser_whitelist.json"
with whitelist_path.open() as whitelist_file:
    PARSE_WHITELIST: dict[str, list[str]] = json.load(whitelist_file)


def peek(stream: BufferedReader, length: int):
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
    "\u200B",
    "\xa0",
]


def get_checksum(number: int):
    """
    Returns horizontal checksum of `number` (sum of all digits).
    """

    number = abs(number)

    return sum(int(digit) for digit in str(number))


def is_camel_case(text: str):
    """
    Checks if `text` is camel case without spaces.
    """

    if " " in text:
        return False

    return any(char.isupper() for char in text[1:]) and not text.isupper()


def is_valid_string(input_string: str):
    """
    Checks if <input_string> is a valid string.
    """

    if not input_string.strip():
        return False

    if is_camel_case(input_string):
        return False

    if "_" in input_string and " " not in input_string:
        return False

    return all((c.isprintable() or c in CHAR_WHITELIST) for c in input_string)
