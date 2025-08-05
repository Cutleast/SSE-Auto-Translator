"""
Copyright (c) Cutleast
"""

from enum import Enum


class TruncateMode(Enum):
    """Truncation mode."""

    Start = "start"
    """
    Truncates the string at the beginning.
    
    Example:     
        >>> truncate_string("Hello, world!", 10, TruncateMode.Start)
        '... world!'
    """

    Middle = "middle"
    """
    Truncates the string in the middle.
    
    Example:     
        >>> truncate_string("Hello, world!", 10, TruncateMode.Middle)
        'Hel...rld!'
    """

    End = "end"
    """
    Truncates the string at the end.
    
    Example:     
        >>> truncate_string("Hello, world!", 10, TruncateMode.End)
        'Hello, ...'
    """


def truncate_string(
    s: str,
    max_length: int,
    mode: TruncateMode = TruncateMode.End,
    placeholder: str = "...",
) -> str:
    """
    Truncates a string to a specified maximum length using a placeholder.

    Args:
        s (str): The original string.
        max_length (int):
            The maximum allowed length of the result (including placeholder).
        mode (TruncateMode, optional):
            Where to truncate the string: start, middle, or end. Defaults to
            TruncateMode.End.
        placeholder (str, optional): The truncation indicator. Defaults to "...".

    Returns:
        str: The truncated string, if necessary.

    Raises:
        ValueError: If max_length is less than the length of the placeholder.
    """

    if len(s) <= max_length:
        return s

    if max_length < len(placeholder):
        raise ValueError(
            "max_length must be at least as long as the placeholder length."
        )

    remaining: int = max_length - len(placeholder)

    match mode:
        case TruncateMode.End:
            return s[:remaining] + placeholder
        case TruncateMode.Start:
            return placeholder + s[-remaining:]
        case TruncateMode.Middle:
            half: int = remaining // 2
            return s[:half] + placeholder + s[-(remaining - half) :]
