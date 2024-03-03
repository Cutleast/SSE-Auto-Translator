"""
This file is part of SEE Auto Translator
and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import logging

import qtpy.QtCore as qtc

print("Importing lingua...")
from lingua import Language, LanguageDetector, LanguageDetectorBuilder

from .string import String


class LangDetector:
    """
    Language detector class.
    """

    detector: LanguageDetector = None
    confidence: int = None

    def __init__(self, app, confidence: int, desired_lang: Language):
        self.app = app
        self.confidence = confidence
        self.desired_lang = desired_lang

        self.detector = (
            LanguageDetectorBuilder.from_languages(Language.ENGLISH, desired_lang)
            .with_minimum_relative_distance(self.confidence)
            .build()
        )

        self.log = logging.getLogger(self.__repr__())
        self.log.addHandler(self.app.log_handler)
        self.log.setLevel(self.app.log.level)

    def __repr__(self):
        return "LangDetector"

    @staticmethod
    def get_available_langs():
        """
        Returns a list of all available languages.
        """

        langs = list(Language.all())
        langs.sort(key=lambda lang: lang.name)

        return langs

    def requires_translation(
        self, strings: list[String], max_string_count: int = 20
    ):
        """
        Checks if plugin file at `plugin_path` requires
        a translation by combining first five strings and
        detecting their language.
        """

        if not len(strings):
            return None

        treshold = (
            max_string_count  # number of strings to combine for more precise detection
        ) - 1
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

        # For Debugging only!!!
        # if not translation_required:
        #     self.log.debug(f"Sample: {detection_string!r}")
        #     self.log.debug(f"Detected Language: {detected_lang}")

        return translation_required

    def detect_lang(self, string: str):
        """
        Detects language of <string> and returns it.
        """

        return self.detector.detect_language_of(string)
