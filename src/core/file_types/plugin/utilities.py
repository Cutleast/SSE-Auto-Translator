"""
Copyright (c) Cutleast
"""

CHAR_WHITELIST: list[str] = [
    "\n",
    "\r",
    "\t",
    "\u200b",
    "\xa0",
    "\u3000",
]
"""Characters accepted in otherwise non-printable plugin strings."""

STRING_BLACKLIST: list[str] = [
    "<p>",
]
"""Known strings that are not displayed to users."""

STRING_WHITELIST: list[str] = [
    "WoollyRhino",
    "CuSith",
]
"""Known displayed strings that resemble internal identifiers."""

IGNORED_STRING_TYPES: list[str] = [
    "BPTD BPTN",
    "FACT FNAM",
    "FACT MNAM",
]
"""Record and subrecord types of strings that are not displayed in-game."""


def is_camel_case(text: str) -> bool:
    """
    Checks whether a text is camelCase or PascalCase without spaces.

    Args:
        text (str): Text to check.

    Returns:
        bool: Whether the text resembles camelCase or PascalCase.
    """

    if len(text) < 3:
        return False

    # The C-level checks run first so that most texts never reach the generator.
    return (
        text.isalnum()
        and not text.isupper()
        and any(char.isupper() and char.isalpha() for char in text[2:])
    )


def is_snake_case(text: str) -> bool:
    """
    Checks whether a text is snake_case without spaces.

    Args:
        text (str): Text to check.

    Returns:
        bool: Whether the text resembles snake_case.
    """

    return " " not in text and "_" in text


def is_valid_string(text: str) -> bool:
    """
    Checks whether a plugin string is likely to appear in-game.

    Args:
        text (str): Text to check.

    Returns:
        bool: Whether the text is likely to require translation.
    """

    if not text.strip() or text in STRING_BLACKLIST:
        return False

    if text in STRING_WHITELIST or "<Alias" in text:
        return True

    if is_camel_case(text) or is_snake_case(text):
        return False

    # Fully printable texts are accepted without checking each character in Python.
    return text.isprintable() or all(
        char.isprintable() or char in CHAR_WHITELIST for char in text
    )
