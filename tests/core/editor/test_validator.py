"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Optional

import pytest

from core.editor.models.diagnostics import TranslationDiagnostics
from core.editor.models.severity import Severity
from core.editor.validator import TranslationValidator
from core.mod_file.context import ModFileContext
from core.translation_context.context import TranslationContext
from core.translation_context.glossary import TranslationGlossary
from core.utilities.game_language import GameLanguage
from tests.setup.paths import PROJECT_PATH


class TestTranslationValidator:
    """
    Tests `core.editor.validator.TranslationValidator`.
    """

    @staticmethod
    def create_context(
        glossary_terms: Optional[dict[str, str]] = None,
    ) -> TranslationContext:
        """
        Creates a minimal translation context with the specified glossary terms.

        Args:
            glossary_terms (Optional[dict[str, str]], optional):
                Map of original terms to their translations. Defaults to None.

        Returns:
            TranslationContext: The translation context.
        """

        return TranslationContext(
            similar_strings=[],
            mod_file_context=ModFileContext(),
            glossary_terms=[
                TranslationGlossary.Term(
                    original=original,
                    translated=translated,
                    source=TranslationGlossary.TermSource.UserGlossary,
                )
                for original, translated in (glossary_terms or {}).items()
            ],
        )

    def test_reports_missing_and_surplus_placeholders(self, tmp_path: Path) -> None:
        """
        Tests that placeholders of the original text whose count differs in the
        translated text are reported with the number of missing occurrences.
        """

        # given
        validator = TranslationValidator(tmp_path)
        context: TranslationContext = TestTranslationValidator.create_context()

        # when
        diagnostics: TranslationDiagnostics = validator.validate_translated_text(
            "Deals <mag> points of damage for <dur> seconds.",
            "Verursacht <mag> Schaden, <mag>.",
            GameLanguage.German,
            context,
        )

        # then
        assert diagnostics.missing_placeholders == {"<dur>": 1, "<mag>": -1}

    def test_accepts_matching_placeholders(self, tmp_path: Path) -> None:
        """
        Tests that no placeholder issues are reported when all placeholders are kept.
        """

        # given
        validator = TranslationValidator(tmp_path)
        context: TranslationContext = TestTranslationValidator.create_context()

        # when
        diagnostics: TranslationDiagnostics = validator.validate_translated_text(
            "Deals <mag> damage for {0} seconds.",
            "Verursacht {0} Sekunden lang <mag> Schaden.",
            GameLanguage.German,
            context,
        )

        # then
        assert diagnostics.missing_placeholders == {}

    @pytest.mark.parametrize(
        "original, translated, expected_severity",
        [
            # lore-specific term (not in the English dictionary)
            ("Travel to Whiterun.", "Reise nach Weisslauf.", Severity.Warning),
            ("Travel to Whiterun.", "Reise nach Weißlauf.", None),
            # ambiguous term at the start of a sentence
            ("Hold the line!", "Haltet die Stellung!", Severity.Notice),
            # ambiguous term capitalized mid-sentence (i.e. a name)
            ("Rule the Hold.", "Beherrsche das Land.", Severity.Warning),
            # ambiguous term written in lowercase mid-sentence
            ("You hold a sword.", "Du hältst ein Schwert.", None),
        ],
    )
    def test_validates_glossary_terms(
        self,
        original: str,
        translated: str,
        expected_severity: Optional[Severity],
        tmp_path: Path,
    ) -> None:
        """
        Tests that glossary terms whose translation is missing are reported with a
        severity depending on whether the term is ambiguous.

        Args:
            original (str): The original text.
            translated (str): The translated text.
            expected_severity (Optional[Severity]):
                The expected severity or None if no issue is expected.
            tmp_path (Path): The temporary folder of the test.
        """

        # given
        validator = TranslationValidator(tmp_path)
        context: TranslationContext = TestTranslationValidator.create_context(
            {"Whiterun": "Weißlauf", "Hold": "Fürstentum"}
        )

        # when
        diagnostics: TranslationDiagnostics = validator.validate_translated_text(
            original, translated, GameLanguage.German, context
        )

        # then
        actual_severities: list[Severity] = [
            issue.severity for issue in diagnostics.glossary_issues
        ]
        if expected_severity is None:
            assert actual_severities == []
        else:
            assert actual_severities == [expected_severity]

    def test_finds_unknown_words(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Tests that misspelled words are reported while words from the context and
        non-English words from the original text are considered known.
        """

        # given
        # the dictionaries are loaded relative to the working directory
        monkeypatch.chdir(PROJECT_PATH)
        validator = TranslationValidator(tmp_path)
        context: TranslationContext = TestTranslationValidator.create_context(
            {"Whiterun": "Weißlauf"}
        )

        # when
        diagnostics: TranslationDiagnostics = validator.validate_translated_text(
            "Bring the sword of Ulfric to Whiterun.",
            "Bringe das Schwrt von Ulfric nach Weißlauf.",
            GameLanguage.German,
            context,
        )

        # then
        assert list(diagnostics.unknown_words) == ["Schwrt"]

    def test_word_added_to_user_dictionary_is_known(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Tests that a word added to the user dictionary is no longer reported and
        persisted in the user data folder.
        """

        # given
        monkeypatch.chdir(PROJECT_PATH)
        validator = TranslationValidator(tmp_path)
        context: TranslationContext = TestTranslationValidator.create_context()
        added_words: list[str] = []
        validator.word_added_to_user_dictionary.connect(added_words.append)

        # when
        validator.add_word_to_user_dictionary("Skooma", GameLanguage.German)
        diagnostics: TranslationDiagnostics = validator.validate_translated_text(
            "Buy some Skooma.", "Kauf etwas Skooma.", GameLanguage.German, context
        )

        # then
        assert added_words == ["Skooma"]
        assert diagnostics.unknown_words == {}
        assert (tmp_path / "hunspell" / "german.dic").is_file()
