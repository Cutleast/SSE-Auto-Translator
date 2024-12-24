"""
Copyright (c) Cutleast
"""

import locale
import logging
from typing import Optional

import win32api

log: logging.Logger = logging.getLogger("Utilities.Localisation")


SUPPORTED_LOCALES: list[str] = ["de_DE", "en_US", "ru_RU", "zh_CN"]


def detect_system_locale() -> Optional[str]:
    """
    Attempts to detect the system locale.

    Returns:
        str: System locale
    """

    log.info("Detecting system locale...")

    system_locale: Optional[str] = None

    try:
        language_id = win32api.GetUserDefaultLangID()
        system_language = locale.windows_locale[language_id]
        log.debug(f"Detected system language: {system_language}")

        if system_language in SUPPORTED_LOCALES:
            system_locale = system_language
        else:
            log.warning(
                "Detected system language is not supported! Falling back to en_US..."
            )

    except Exception as ex:
        log.error(f"Failed to get system language: {ex}", exc_info=ex)

    return system_locale
