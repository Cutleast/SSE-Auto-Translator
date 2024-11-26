"""
This file is part of SEE Auto Translator
and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging

from lingua import Language, LanguageDetector, LanguageDetectorBuilder

from .string import String


class LangDetector:
    """
    Language detector class.
    """

    detector: LanguageDetector = None
    confidence: int = None

    log = logging.getLogger("Utilities.LangDetector")

    def __init__(self, app, confidence: int, desired_lang: Language):
        self.app = app
        self.confidence = confidence
        self.desired_lang = desired_lang

        self.detector = (
            LanguageDetectorBuilder.from_languages(Language.ENGLISH, desired_lang)
            .with_minimum_relative_distance(self.confidence)
            .build()
        )

    @staticmethod
    def get_available_langs():
        """
        Returns a list of all available languages.
        """

        langs = list(Language.all())
        langs.sort(key=lambda lang: lang.name)

        return langs

    def requires_translation(self, strings: list[String], max_string_count: int = 40):
        """
        Checks if plugin file at `plugin_path` requires
        a translation by combining first five strings and
        detecting their language.
        """

        if not len(strings):
            return None

        # Number of strings to combine for more precise detection
        treshold = max_string_count - 1

        detection_string = ""
        c = 0
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

        detected_lang = self.detect_lang(detection_string)
        translation_required = detected_lang != self.desired_lang
        self.log.info(f"Translation required: {translation_required}")

        return translation_required

    def detect_lang(self, string: str):
        """
        Detects language of <string> and returns it.
        """

        return self.detector.detect_language_of(string)
