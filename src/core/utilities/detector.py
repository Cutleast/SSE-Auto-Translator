"""
Copyright (c) Cutleast
"""

import logging
from typing import Optional

from lingua import Language, LanguageDetector, LanguageDetectorBuilder

from core.database.string import String


class LangDetector:
    """
    Language detector class.
    """

    detector: LanguageDetector
    confidence: float

    log: logging.Logger = logging.getLogger("Utilities.LangDetector")

    def __init__(self, confidence: float, desired_lang: Language):
        self.confidence = confidence
        self.desired_lang = desired_lang

        builder: LanguageDetectorBuilder = LanguageDetectorBuilder.from_languages(
            Language.ENGLISH, desired_lang
        )
        builder.with_minimum_relative_distance(self.confidence)
        self.detector = builder.build()

    @staticmethod
    def get_available_langs() -> list[Language]:
        """
        Gets a list of all available languages.

        Returns:
            list[Language]: List of languages.
        """

        langs: list[Language] = list(Language.all())
        langs.sort(key=lambda lang: lang.name)

        return langs

    def requires_translation(
        self, strings: list[String], max_string_count: int = 40
    ) -> bool:
        """
        Checks if a plugin requires a translation.

        Args:
            strings (list[String]): List of strings to check.
            max_string_count (int, optional):
                Maximum number of strings to check. Defaults to 40.

        Returns:
            bool: True if a translation is required, False otherwise.
        """

        if not len(strings):
            return False

        # Number of strings to combine for more precise detection
        treshold: int = max_string_count - 1

        detection_string: str = ""
        c: int = 0
        for string_data in strings:
            if string_data.original_string not in detection_string:
                detection_string += string_data.original_string + "\n"
                c += 1
                if c == treshold:
                    break
        else:
            self.log.warning(
                f"Treshold not reached! Plugin has only {c} different string(s). Reliable detection not possible!"
            )

        detected_lang: Optional[Language] = self.detect_lang(detection_string)
        translation_required: bool = detected_lang != self.desired_lang
        self.log.info(f"Translation required: {translation_required}")

        return translation_required

    def detect_lang(self, string: str) -> Optional[Language]:
        """
        Attempts to detect the language of a string.

        Args:
            string (str): String to detect language of.

        Returns:
            Optional[Language]: Detected language or None if unknown.
        """

        return self.detector.detect_language_of(string)
