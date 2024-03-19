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
    "\u3000",
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

    if len(text) < 3:
        return False

    return (
        any(char.isupper() and char.isalpha() for char in text[2:])
        and not text.isupper()
        and text.isalpha()
    )


def is_snake_case(text: str):
    """
    Checks if `text` is snake case without spaces.
    """

    return " " not in text and "_" in text


def is_valid_string(text: str):
    """
    Checks if <text> is a valid string.
    """

    if not text.strip():
        return False

    if "<Alias" in text:
        return True

    if is_camel_case(text) or is_snake_case(text):
        return False

    return all(char.isprintable() or char in CHAR_WHITELIST for char in text)
