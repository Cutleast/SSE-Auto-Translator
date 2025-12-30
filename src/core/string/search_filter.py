"""
Copyright (c) Cutleast
"""

from typing import Optional, TypedDict

from core.string.types import String


class SearchFilter(TypedDict, total=False):
    """
    Typed dictionary for search filters.
    """

    id: str
    original: str
    string: str


def matches_filter(filter: SearchFilter, string: String) -> bool:
    """
    Checks if a string matches a filter.

    Args:
        filter (SearchFilter): The filter to check.
        string (String): The string to check.

    Returns:
        bool: True if the string matches the filter, False otherwise.
    """

    id_filter: Optional[str] = filter.get("id")
    original_filter: Optional[str] = filter.get("original")
    string_filter: Optional[str] = filter.get("string")

    matching: bool = True

    if id_filter and matching:
        matching = id_filter in string.display_id

    if original_filter and matching:
        matching = original_filter.lower() in string.original.lower()

    if string_filter and matching and string.string is not None:
        matching = string_filter.lower() in string.string.lower()
    elif string_filter:
        matching = False

    return matching
