"""
Copyright (c) Cutleast
"""

from enum import Enum
from typing import Optional, override


class GameLanguage(Enum):
    """Enum for the languages supported as target language for the game."""

    Chinese = "Chinese"
    French = "French"
    German = "German"
    Italian = "Italian"
    Japanese = "Japanese"
    Korean = "Korean"
    Polish = "Polish"
    Portuguese = "Portuguese"
    Russian = "Russian"
    Spanish = "Spanish"
    Turkish = "Turkish"

    @override
    def __str__(self) -> str:
        return self.name

    @property
    def iso_code(self) -> str:
        """The ISO code of this language."""

        ISO_CODES: dict[GameLanguage, str] = {
            GameLanguage.Chinese: "zh_CN",
            GameLanguage.French: "fr_FR",
            GameLanguage.German: "de_DE",
            GameLanguage.Italian: "it_IT",
            GameLanguage.Japanese: "jp_JP",
            GameLanguage.Korean: "ko_KR",
            GameLanguage.Polish: "pl_PL",
            GameLanguage.Portuguese: "pt_BR",
            GameLanguage.Russian: "ru_RU",
            GameLanguage.Spanish: "es_ES",
            GameLanguage.Turkish: "tr_TR",
        }

        return ISO_CODES[self]

    @property
    def uses_word_boundaries(self) -> bool:
        """
        Whether words are separated by spaces, which is not the case for Chinese and
        Japanese.
        """

        return self not in (GameLanguage.Chinese, GameLanguage.Japanese)

    @property
    def stemmer_algorithm(self) -> Optional[str]:
        """The name of the Snowball stemmer algorithm or None if there is none."""

        if self in (GameLanguage.Chinese, GameLanguage.Japanese, GameLanguage.Korean):
            return None

        return self.id

    @property
    def min_stem_length(self) -> int:
        """
        The minimum length of a word stem to be searched within other words, as shorter
        stems match too many unrelated words.
        """

        # Hangul syllables carry about as much information as two latin letters
        return 2 if self == GameLanguage.Korean else 4

    @property
    def loose_suffixes(self) -> tuple[str, ...]:
        """
        Suffixes that the Snowball stemmer of this language does not remove from every
        word, like the "s" of genitives and loanword plurals in "Vaerminas" or "Jarls".
        """

        if self in (
            GameLanguage.German,
            GameLanguage.Italian,
            GameLanguage.Portuguese,
            GameLanguage.Spanish,
        ):
            return ("s",)

        return ()

    @property
    def id(self) -> str:
        """The id of this language."""

        return self.name.lower()
