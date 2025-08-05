"""
Copyright (c) Cutleast
"""

import logging
from typing import Optional

import spylls.hunspell as hunspell

from core.cache.function_cache import FunctionCache


class SpellChecker:
    """
    Class for checking the spelling of words using a Hunspell dictionary.
    """

    log: logging.Logger = logging.getLogger("SpellChecker")

    __dictionary: Optional[hunspell.Dictionary]

    def __init__(self, language: str) -> None:
        """
        Args:
            language (str): The lowered name of the language to load the dictionary for.
        """

        try:
            self.__dictionary = self._load_dictionary(language)
            self.log.info(f"Hunspell dictionary loaded for: {language}")
        except (FileNotFoundError, OSError) as ex:
            self.log.exception(
                f"Failed to load dictionary for language '{language}': {ex}"
            )
            self.__dictionary = None

    def is_correct(self, word: str) -> bool:
        """
        Checks if the specified word is correctly spelled.
        Also returns `True` if no dictionary is loaded.

        Args:
            word (str): The word to check.

        Returns:
            bool: `True` if the word is correctly spelled, `False` otherwise.
        """

        return self.__dictionary is None or self.__dictionary.lookup(word)

    def get_suggestions(self, word: str) -> list[str]:
        """
        Gets a list of suggestions for the specified word.
        Returns an empty list if no dictionary is loaded.

        TODO: Optimize this function or move it to a separate thread

        Args:
            word (str): The word to get suggestions for.

        Returns:
            list[str]: A list of suggested words.
        """

        if self.__dictionary:
            return list(self.__dictionary.suggest(word))

        return []

    @staticmethod
    @FunctionCache.cache
    def _load_dictionary(language: str) -> hunspell.Dictionary:
        """
        Loads the Hunspell dictionary for the specified language.

        Args:
            language (str): The language to load the dictionary for.

        Returns:
            hunspell.Dictionary: The loaded Hunspell dictionary.
        """

        return hunspell.Dictionary.from_files(f"./res/hunspell/{language}")
