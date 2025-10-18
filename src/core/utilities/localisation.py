"""
Copyright (c) Cutleast
"""

import locale
import logging
from enum import Enum
from typing import Optional

import win32api

from core.utilities.game_language import GameLanguage


class Language(Enum):
    """
    Enum for supported application languages.
    """

    System = "System"
    German = "de_DE"
    English = "en_US"
    # Russian = "ru_RU"
    # Chinese = "zh_CN"


class LocalisationUtils:
    """
    Class for utilities related to localisation.
    """

    log: logging.Logger = logging.getLogger("LocalisationUtils")

    @classmethod
    def detect_preferred_lang(cls) -> Optional[str]:
        """
        Attempts to detect the preferred language for the translations and the game based
        on the system locale.

        Returns:
            Optional[str]:
                Preferred language or None if the system language is not supported.
        """

        cls.log.info("Detecting system language...")

        langs: dict[str, str] = {lang.iso_code: lang.id for lang in GameLanguage}
        pref_lang: Optional[str] = None

        try:
            language_id: int = win32api.GetUserDefaultLangID()
            system_language: str = locale.windows_locale[language_id]
            cls.log.debug(f"Detected system language: {system_language}")

            pref_lang = langs.get(system_language)
            if pref_lang is None:
                cls.log.warning("Detected system language is not supported!")

        except Exception as ex:
            cls.log.error(f"Failed to get system language: {ex}", exc_info=ex)

        return pref_lang

    @classmethod
    def detect_system_locale(cls) -> Optional[str]:
        """
        Attempts to detect the system locale.

        Returns:
            str: System locale
        """

        cls.log.info("Detecting system locale...")

        system_locale: Optional[str] = None

        try:
            language_id = win32api.GetUserDefaultLangID()
            system_language = locale.windows_locale[language_id]
            cls.log.debug(f"Detected system language: {system_language}")

            if system_language in [lang.value for lang in Language]:
                system_locale = system_language
            else:
                cls.log.warning(
                    "Detected system language is not supported! Falling back to en_US..."
                )

        except Exception as ex:
            cls.log.error(f"Failed to get system language: {ex}", exc_info=ex)

        return system_locale
