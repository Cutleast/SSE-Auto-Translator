"""
Copyright (c) Cutleast
"""

import logging
from typing import Optional

from cutleast_core_lib.core.cache.function_cache import FunctionCache
from hunspell import Hunspell


class SpellChecker:
    """
    Class for checking the spelling of words using a Hunspell dictionary.
    """

    log: logging.Logger = logging.getLogger("SpellChecker")

    __hunspell: Optional[Hunspell]

    def __init__(self, language: str) -> None:
        """
        Args:
            language (str): The lowered name of the language to load the dictionary for.
        """

        try:
            self.__hunspell = self._load_hunspell(language)
            self.log.info(f"Hunspell dictionary loaded for: {language}")
        except (FileNotFoundError, OSError) as ex:
            self.log.exception(
                f"Failed to load dictionary for language '{language}': {ex}"
            )
            self.__hunspell = None

    def is_correct(self, word: str) -> bool:
        """
        Checks if the specified word is correctly spelled.
        Also returns `True` if no dictionary is loaded.

        Args:
            word (str): The word to check.

        Returns:
            bool: `True` if the word is correctly spelled, `False` otherwise.
        """

        return self.__hunspell is None or self.__hunspell.spell(word)

    def get_suggestions(self, word: str) -> list[str]:
        """
        Gets a list of suggestions for the specified word.
        Returns an empty list if no dictionary is loaded.

        Args:
            word (str): The word to get suggestions for.

        Returns:
            list[str]: A list of suggested words.
        """

        if self.__hunspell:
            return list(self.__hunspell.suggest(word))

        return []

    def add_word_to_dictionary(self, word: str) -> None:
        """
        Adds a word to the current dictionary.

        Args:
            word (str): The word to add.
        """

        if self.__hunspell:
            self.__hunspell.add(word)

    @staticmethod
    @FunctionCache.cache
    def _load_hunspell(language: str) -> Hunspell:
        """
        Loads the Hunspell dictionary for the specified language.

        Args:
            language (str): The language to load the dictionary for.

        Returns:
            Hunspell: The loaded Hunspell dictionary.
        """

        return Hunspell(language, hunspell_data_dir="./res/hunspell")
