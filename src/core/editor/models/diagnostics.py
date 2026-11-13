"""
Copyright (c) Cutleast
"""

from functools import cached_property

from pydantic import BaseModel, Field
from PySide6.QtWidgets import QApplication

from core.utilities.text import Occurrences

from .glossary_issue import GlossaryIssue
from .severity import Severity


class TranslationDiagnostics(BaseModel, frozen=True):
    """
    Translation diagnostics of a single editor string.
    """

    unknown_words: dict[str, list[str]] = Field(default_factory=dict)
    """
    Words (and correction suggestions) that are not in the target language dictionary.
    Words occurring in the context, like names and official terms, are considered known.
    """

    glossary_issues: list[GlossaryIssue] = Field(default_factory=list)
    """
    Terms from the glossary whose translation is missing in the translated text, because
    they were translated differently or lost.
    """

    missing_placeholders: Occurrences = Field(default_factory=dict)
    """
    Placeholders that are in the original text but got lost in the translation and their
    occurence count.
    """

    @cached_property
    def severity(self) -> Severity:
        """The severity of these diagnostics."""

        if self.missing_placeholders:
            return Severity.Error

        if self.glossary_issues:
            return max(issue.severity for issue in self.glossary_issues)

        if self.unknown_words:
            return Severity.Notice

        return Severity.Passed

    def get_localized_summary(self) -> str:
        """
        Returns:
            str: A localized text summarizing this diagnostics result.
        """

        text: str = (
            QApplication.translate("TranslationDiagnostics", "Severity")
            + ": "
            + self.severity.get_localized_name()
        )

        if self.unknown_words:
            text += (
                "\n"
                + QApplication.translate("TranslationDiagnostics", "Unknown words")
                + ": "
                + str(len(self.unknown_words))
            )

        if self.glossary_issues:
            text += (
                "\n"
                + QApplication.translate("TranslationDiagnostics", "Glossary issues")
                + ": "
                + str(len(self.glossary_issues))
            )

        if self.missing_placeholders:
            text += (
                "\n"
                + QApplication.translate(
                    "TranslationDiagnostics", "Missing placeholders"
                )
                + ": "
                + str(sum(self.missing_placeholders.values()))
            )

        return text
