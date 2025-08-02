"""
Copyright (c) Cutleast
"""

from typing import Optional

import pytest

from core.scanner.detector import LangDetector, Language
from core.string.string import String


class TestLangDetector:
    """
    Tests `core.scanner.detector.LangDetector`.
    """

    def create_string(self, text: str) -> String:
        return String(
            editor_id="TestString",
            form_id="00123456|Skyrim.esm",
            type="BOOK FULL",
            original=text,
        )

    def setup(self, language: Language, confidence: float = 0.8) -> LangDetector:
        """
        Initializes a language detector for testing purposes.
        """

        return LangDetector(confidence, language)

    TEST_CASES: list[tuple[str, Language, Language]] = [
        ("Hello World, how are you?", Language.GERMAN, Language.ENGLISH),
        ("Hallo Welt, wie gehts?", Language.GERMAN, Language.GERMAN),
        ("Bonjour, comment ça va?", Language.FRENCH, Language.FRENCH),
    ]

    @pytest.mark.parametrize("text, target_language, expected_output", TEST_CASES)
    def test_detect_lang(
        self, text: str, target_language: Language, expected_output: Language
    ) -> None:
        """
        Tests `LangDetector.requires_translation`.
        """

        # given
        detector: LangDetector = self.setup(target_language)

        # when
        real_output: Optional[Language] = detector.detect_lang(text)

        # then
        assert real_output == expected_output
