"""
Copyright (c) Cutleast
"""

from enum import Enum


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
        }

        return ISO_CODES[self]

    @property
    def id(self) -> str:
        """The id of this language."""

        return self.name.lower()
