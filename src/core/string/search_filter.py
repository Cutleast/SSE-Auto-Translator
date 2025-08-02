"""
Copyright (c) Cutleast
"""

from typing import Optional, TypedDict

from .string import String


class SearchFilter(TypedDict, total=False):
    """
    Typed dictionary for search filters.
    """

    type: str
    form_id: str
    editor_id: str
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

    type_filter: Optional[str] = filter.get("type")
    form_id_filter: Optional[str] = filter.get("form_id")
    editor_id_filter: Optional[str] = filter.get("editor_id")
    original_filter: Optional[str] = filter.get("original")
    string_filter: Optional[str] = filter.get("string")

    matching: bool = True

    if type_filter:
        matching = type_filter.lower() in string.type.lower()

    if form_id_filter and matching:
        matching = form_id_filter.lower() in (string.form_id or "").lower()

    if editor_id_filter and matching and string.editor_id is not None:
        matching = editor_id_filter.lower() in string.editor_id.lower()
    elif editor_id_filter:
        matching = False

    if original_filter and matching:
        matching = original_filter.lower() in string.original.lower()

    if string_filter and matching and string.string is not None:
        matching = string_filter.lower() in string.string.lower()
    elif string_filter:
        matching = False

    return matching
