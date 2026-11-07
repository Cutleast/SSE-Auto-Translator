"""
Copyright (c) Cutleast
"""

from typing import override

from pydantic import BaseModel


class GlossaryTerm(BaseModel, validate_assignment=True):
    """
    An editable term of the user's glossary for the LLM translator.
    """

    original: str
    """The original term."""

    translation: str
    """The translation of the term."""

    @override
    def __str__(self) -> str:
        return f"{self.original} → {self.translation}"
