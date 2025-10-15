"""
Copyright (c) Cutleast
"""

import logging
from pathlib import Path
from typing import Optional

from cutleast_core_lib.core.cache.function_cache import FunctionCache
from hunspell import Hunspell


class SpellChecker:
    """
    Class for checking the spelling of words using a Hunspell dictionary.
    """

    log: logging.Logger = logging.getLogger("SpellChecker")

    __hunspell: Optional[Hunspell]
    __user_dic_path: Path

    def __init__(self, language: str, user_data_path: Path) -> None:
        """
        Args:
            language (str): The lowered name of the language to load the dictionary for.
            user_data_path (Path): Path to the user data directory.
        """

        self.__user_dic_path = user_data_path / "hunspell" / f"{language}.dic"

        try:
            self.__hunspell = self._load_hunspell(language)
            self.__load_user_dictionary()
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
        Adds a word to the custom user dictionary (persistently).

        Args:
            word (str): The word to add.
        """

        if not self.__hunspell:
            return

        word = word.strip()
        if not word:
            return

        if not self.__user_dic_path.is_file():
            self.__user_dic_path.parent.mkdir(parents=True, exist_ok=True)
            self.__user_dic_path.write_text("0\n", encoding="utf-8")

        # Read all existing words
        words: set[str] = set(
            line.strip()
            for line in self.__user_dic_path.read_text(encoding="utf-8").splitlines()[
                1:
            ]
        )

        # Add new word if not already present
        if word not in words:
            words.add(word)

            # Rewrite file with updated count
            content = f"{len(words)}\n" + "\n".join(sorted(words))
            self.__user_dic_path.write_text(content, encoding="utf-8")
            self.__hunspell.add(word)
            self.log.info(f"Added word '{word}' to user dictionary.")

    def __load_user_dictionary(self) -> None:
        """
        Loads the custom user dictionary if it exists.
        """

        if not self.__hunspell:
            return

        if self.__user_dic_path.is_file():
            try:
                self.__hunspell.add_dic(str(self.__user_dic_path))
                self.log.info(f"Loaded user dictionary: {self.__user_dic_path}")
            except Exception as ex:
                self.log.warning(
                    f"Failed to load user dictionary {self.__user_dic_path}: {ex}"
                )

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
