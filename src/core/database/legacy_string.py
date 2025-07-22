"""
Copyright (c) Cutleast
"""

from dataclasses import field
from enum import Enum, auto

from pydantic.dataclasses import dataclass


@dataclass
class LegacyString:
    """
    Legacy version of the String class for deserialization of old pickle files.

    **DO NOT USE THIS CLASS!**
    """

    form_id: str
    type: str
    original_string: str
    translated_string: str | None = None
    index: int | None = None
    editor_id: str | None = None

    class Status(Enum):
        NoneStatus = auto()
        NoTranslationRequired = auto()
        TranslationComplete = auto()
        TranslationIncomplete = auto()
        TranslationRequired = auto()

    status: Status = field(default=Status.NoneStatus)
