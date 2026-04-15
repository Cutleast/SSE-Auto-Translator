"""
Copyright (c) Cutleast
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, cast, final

from cutleast_core_lib.core.cache.cache import Cache
from cutleast_core_lib.core.utilities.hash import sha256_hash

from core.config.translator_config import TranslatorConfig
from core.utilities.game_language import GameLanguage


class Translator(ABC):
    """
    Base class for translator APIs that generate automated machine translations.

    **Note to implementers**: The instances should be stateless.
    """

    CACHE_FOLDER = Path("translator_cache")
    """The subfolder within the cache folder to store cached API translations."""

    CACHE_MAX_AGE: int = 60 * 60 * 72  # 72 hours
    """Maximum age of cached translations in seconds."""

    _config: TranslatorConfig
    """The app-wide translator configuration."""

    log: logging.Logger

    def __init__(self, config: TranslatorConfig) -> None:
        """
        Args:
            config (TranslatorConfig): The app-wide translator configuration.
        """

        self._config = config

        self.log = logging.getLogger(self.__class__.__name__)

    @final
    @Cache.persistent_cache(
        cache_subfolder=CACHE_FOLDER,
        id_generator=lambda self, text, dst: cast(Translator, self).get_cache_id(
            text, dst
        ),
        max_age=CACHE_MAX_AGE,
    )
    def translate(self, text: str, dst: GameLanguage) -> str:
        """
        Translates a single text from a source language to a destination language.

        Args:
            text (str): The text to translate.
            dst (GameLanguage): The destination language.

        Returns:
            str: The translated text.
        """

        return self.translate_uncached(text, dst)

    def _get_from_cache(self, text: str, dst: GameLanguage) -> Optional[str]:
        """
        Gets a translation result from the cache.

        Args:
            text (str): The text to translate.
            dst (GameLanguage): The destination language.

        Returns:
            str: The translated text.
        """

        cache_file_path: Path = Translator.CACHE_FOLDER / (
            Translator.get_cache_id(self, text, dst) + ".cache"
        )
        return Cache.get_from_cache(
            cache_file_path, max_age=Translator.CACHE_MAX_AGE, default=None
        )

    def _add_to_cache(self, text: str, translation: str, dst: GameLanguage) -> None:
        """
        Adds a translation result to the cache.

        Args:
            text (str): The text to translate.
            translation (str): The translated text.
            dst (GameLanguage): The destination language.
        """

        cache_file_path: Path = Translator.CACHE_FOLDER / (
            Translator.get_cache_id(self, text, dst) + ".cache"
        )
        Cache.save_to_cache(cache_file_path, translation)

    @abstractmethod
    def translate_uncached(self, text: str, dst: GameLanguage) -> str:
        """
        Translates a single text from a source language to a destination language.

        Args:
            text (str): The text to translate.
            dst (GameLanguage): The destination language.

        Returns:
            str: The translated text.
        """

    def mass_translate(self, texts: list[str], dst: GameLanguage) -> dict[str, str]:
        """
        Translates multiple texts from a source language to a destination language.

        Args:
            texts (list[str]): The texts to translate.
            dst (GameLanguage): The destination language.

        Returns:
            dict[str, str]: Mapping of original text to its translation.
        """

        return {text: self.translate(text, dst) for text in texts}

    def get_cache_id(self: Translator, text: str, dst: GameLanguage) -> str:
        """
        Generates an ID for a cache file for a single translation request.

        Args:
            text (str): The text to translate.
            dst (GameLanguage): The destination language.

        Returns:
            str: The translated text.
        """

        data: str = f"{self.__class__.__name__}-{text}-{dst.name}"

        return sha256_hash(data.encode())
