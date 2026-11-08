"""
Copyright (c) Cutleast
"""

import re
from pathlib import Path
from threading import Lock
from typing import Optional

from PySide6.QtCore import QObject, Signal

from core.translation_context.context import TranslationContext
from core.translation_context.glossary import TranslationGlossary
from core.utilities.game_language import GameLanguage
from core.utilities.spell_checker import SpellChecker
from core.utilities.text import (
    Occurrences,
    find_all_terms,
    find_term,
    get_placeholders,
    get_words,
    is_at_sentence_start,
    plain_text,
)

from .models import GlossaryIssue, Severity, TranslationDiagnostics


class TranslationValidator(QObject):
    """
    Validates translation results against their context (placeholders, glossary terms,
    misspelled words, etc.).
    """

    word_added_to_user_dictionary = Signal(str)
    """
    Signal emitted when a word has been added to the user dictionary.

    Args:
        word (str): The word that was added.
    """

    SPELL_CHECK_LOCK = Lock()
    """Lock that serializes the spell checks of parallel requests."""

    __user_data_path: Path
    __english_spell_checker: SpellChecker
    __spell_checkers: dict[GameLanguage, SpellChecker]

    def __init__(self, user_data_path: Path) -> None:
        """
        Args:
            user_data_path (Path): Path to the user data directory.
        """

        super().__init__()

        self.__user_data_path = user_data_path
        self.__english_spell_checker = SpellChecker(language=None, user_data_path=None)
        self.__spell_checkers = {}

    def validate_translated_text(
        self,
        original: str,
        translated: str,
        dst: GameLanguage,
        context: TranslationContext,
    ) -> TranslationDiagnostics:
        """
        Runs diagnostics on the translation of an original text against its context.

        Args:
            original (str): The original text.
            translated (str): The translated text.
            dst (GameLanguage): The destination language.
            context (TranslationContext):
                The translation context of the string being edited.

        Returns:
            TranslationDiagnostics: The diagnostics result.
        """

        unknown_words: dict[str, list[str]] = self.__find_unknown_words(
            translated, original, dst, context
        )
        glossary_issues: list[GlossaryIssue] = self.__validate_glossary_terms(
            translated, original, context.glossary_terms
        )
        missing_placeholders: Occurrences = self.__validate_placeholders(
            translated, original
        )

        return TranslationDiagnostics(
            unknown_words=unknown_words,
            glossary_issues=glossary_issues,
            missing_placeholders=missing_placeholders,
        )

    def __validate_placeholders(self, translated: str, original: str) -> Occurrences:
        """
        Counts special placeholders in a translated and original text and returns those
        that occur in the original but not in the translated text.

        Args:
            translated (str): The translated text.
            original (str): The original text.

        Returns:
            Occurrences: The placeholder occurrences that are missing in the translation.
        """

        original_placeholders: Occurrences = get_placeholders(original)
        translated_placeholders: Occurrences = get_placeholders(translated)

        missing_placeholders: Occurrences = {}
        for placeholder, expected_count in original_placeholders.items():
            actual_count: int = translated_placeholders.get(placeholder, 0)
            diff: int = expected_count - actual_count
            if diff != 0:
                missing_placeholders[placeholder] = diff

        return missing_placeholders

    def __validate_glossary_terms(
        self, translated: str, original: str, terms: list[TranslationGlossary.Term]
    ) -> list[GlossaryIssue]:
        """
        Finds glossary terms that occur in the original text but whose translation is
        missing in the translated text, because they were translated differently or lost.
        Longer terms take precedence over shorter terms they contain.

        Args:
            translated (str): The translated text.
            original (str): The original text.
            terms (list[TranslationGlossary.Term]): The glossary terms.

        Returns:
            list[GlossaryIssue]: A list of glossary-related issues.
        """

        plain_original: str = plain_text(original)
        remaining_original: str = plain_original
        issues: list[GlossaryIssue] = []

        for term in sorted(terms, key=lambda t: len(t.original), reverse=True):
            original_matches: list[re.Match[str]] = find_all_terms(
                remaining_original, term.original
            )
            if not original_matches:
                continue

            # hide the matches so that shorter terms contained in them are not checked
            # again
            for match in original_matches:
                remaining_original = (
                    remaining_original[: match.start()]
                    + " " * len(match.group())
                    + remaining_original[match.end() :]
                )

            if find_term(translated, term.translated) is not None:
                continue

            with TranslationValidator.SPELL_CHECK_LOCK:
                # single-worded glossary terms that appear in the English dictionary are
                # considered ambiguous and not lore-specific
                ambiguous: bool = len(
                    get_words(term.original)
                ) == 1 and self.__english_spell_checker.is_correct(term.original.lower())

            severity: Optional[Severity] = None
            if not ambiguous:
                severity = Severity.Warning
            else:
                sentence_starts: list[bool] = [
                    is_at_sentence_start(plain_original, match)
                    for match in original_matches
                ]
                if any(  # check for words that are capitalized mid-sentence (i.e. names)
                    match.group()[0].isupper() and not sentence_start
                    for match, sentence_start in zip(original_matches, sentence_starts)
                ):
                    severity = Severity.Warning
                elif any(sentence_starts):
                    severity = Severity.Notice

            if severity is not None:
                issues.append(GlossaryIssue(term=term, severity=severity))

        return issues

    def __find_unknown_words(
        self,
        translation: str,
        original: str,
        dst: GameLanguage,
        context: TranslationContext,
    ) -> dict[str, list[str]]:
        """
        Finds the words of a translation that are not in the dictionary of the target
        language. Words occurring in the context, like names and official terms, are
        considered known.

        Args:
            translation (str): The translated text.
            original (str): The original text.
            dst (GameLanguage): The target language.
            context (TranslationContext): The translation context of the text.

        Returns:
            dict[str, list[str]]:
                The unknown words in the order of their occurrence and a list of
                suggestions.
        """

        known_words: set[str] = {
            word.lower()
            for known_text in (
                self.__get_non_english_words(original)
                + self.__get_known_context_terms(context)
            )
            for word in get_words(plain_text(known_text))
        }
        words: list[str] = get_words(plain_text(translation))

        # Hunspell is not thread-safe and requests may be processed in parallel
        with TranslationValidator.SPELL_CHECK_LOCK:
            spell_checker: SpellChecker = self.__get_spell_checker(dst)

            return {
                word: spell_checker.get_suggestions(word)
                for word in dict.fromkeys(words)
                if word.lower() not in known_words and not spell_checker.is_correct(word)
            }

    def __get_spell_checker(self, language: GameLanguage) -> SpellChecker:
        if language not in self.__spell_checkers:
            self.__spell_checkers[language] = SpellChecker(
                language.id, self.__user_data_path
            )

        return self.__spell_checkers[language]

    def __get_non_english_words(self, text: str) -> list[str]:
        with TranslationValidator.SPELL_CHECK_LOCK:
            return [
                word
                for word in get_words(text)
                if not self.__english_spell_checker.is_correct(word)
            ]

    def __get_known_context_terms(self, context: TranslationContext) -> list[str]:
        texts: list[str] = [term.translated for term in context.glossary_terms]
        texts += [
            similar_string.string.string
            for similar_string in context.similar_strings
            if similar_string.string.string is not None
        ]
        texts += [
            related_string.string.string
            for related_string in context.mod_file_context.related_strings
            if related_string.string.string is not None
        ]

        return texts

    def add_word_to_user_dictionary(self, word: str, language: GameLanguage) -> None:
        """
        Adds a word to the user dictionary.

        Args:
            word (str): The word to add.
            language (GameLanguage): The language of the word.
        """

        spell_checker: SpellChecker = self.__get_spell_checker(language)
        spell_checker.add_word_to_dictionary(word)
        self.word_added_to_user_dictionary.emit(word)
