"""
Copyright (c) Cutleast
"""

from typing import Optional

from pydantic import BaseModel

from core.translation_context.glossary import TranslationGlossary

from .severity import Severity


class GlossaryIssue(BaseModel, frozen=True):
    """
    A glossary term whose translation is missing in a translated text.
    """

    term: TranslationGlossary.Term
    """The glossary term."""

    severity: Severity
    """How certain it is that the term should have been applied."""

    reason: Optional[str] = None
    """The translator's reason for not applying the term, if provided."""
