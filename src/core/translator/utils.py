"""
Copyright (c) Cutleast
"""

import json
from typing import Optional

from cutleast_core_lib.core.utilities.truncate import truncate_string


def format_pair(original: str, translation: Optional[str], max_length: int) -> str:
    """
    Formats an original string and its translation, if any, as a single line.

    Args:
        original (str): The original string.
        translation (Optional[str]): The translated string or None.
        max_length (int): The maximum length of each side.

    Returns:
        str: The formatted line.
    """

    formatted: str = format_string(original, max_length)
    if translation is not None and translation != original:
        formatted += " -> " + format_string(translation, max_length)

    return formatted


def format_string(text: str, max_length: int) -> str:
    """
    Truncates and quotes a context string so that its boundaries and line breaks are
    unambiguous.

    Args:
        text (str): The string to format.
        max_length (int): The maximum length of the formatted string.

    Returns:
        str: The formatted string.
    """

    return json.dumps(truncate_string(text, max_length), ensure_ascii=False)
