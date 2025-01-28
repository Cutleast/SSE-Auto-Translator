"""
Copyright (c) Cutleast
"""

import logging
from typing import Optional

log = logging.getLogger("Utilities")


def is_valid_hex_color(color_code: str) -> bool:
    """
    Checks if a string is a valid hex color code.

    Args:
        color_code (str): String to check.

    Returns:
        bool: True if string is a valid hex color code, False otherwise.
    """

    color_code = color_code.removeprefix("#")

    if (len(color_code) == 6) or (len(color_code) == 8):
        try:
            int(color_code, 16)
            return True

        except ValueError:
            return False
    else:
        return False


def trim_string(text: str, max_length: int = 100) -> str:
    """
    Returns raw representation (for eg. "\\n" instead of a line break) of a text
    trimmed to a specified number of characters.
    Appends "..." suffix if the text was longer than the specified length.

    Args:
        text (str): String to trim.
        max_length (int, optional): Maximum length of trimmed string. Defaults to 100.

    Returns:
        str: Trimmed string
    """

    if not isinstance(text, str):
        return str(text)

    if len(text) > max_length:
        trimmed_text = text[: max_length - 3] + "..."
        return f"{trimmed_text!r}"[1:-1]

    return f"{text!r}"[1:-1]


def matches_filter(
    text: str, filter: Optional[str], case_sensitive: bool = False
) -> bool:
    """
    Checks if a string matches a filter.

    Args:
        text (str): Text to check.
        filter (Optional[str]): Filter to check against.
        case_sensitive (bool, optional): Case sensitivity. Defaults to False.

    Returns:
        bool: True if string matches filter or filter is None, False otherwise.
    """

    if filter is None:
        return True

    if not case_sensitive:
        text = text.lower()
        filter = filter.lower()

    return filter.strip() in text.strip()
