"""
Copyright (c) Cutleast
"""

from typing import Optional, cast, final, override

import googletrans
import googletrans.models
from cutleast_core_lib.core.utilities.typing_utils import checked_cast
from cutleast_core_lib.core.utilities.unique import unique

from core.config.translator_config import TranslatorConfig
from core.utilities.game_language import GameLanguage

from .translator import Translator


@final
class GoogleTranslator(Translator):
    """
    API class for translating texts with Google Translator.
    """

    LANG_OVERRIDES: dict[GameLanguage, str] = {
        GameLanguage.Chinese: "zh-cn",
    }

    __translator: googletrans.Translator

    @override
    def __init__(self, config: TranslatorConfig) -> None:
        super().__init__(config)

        self.__translator = googletrans.Translator()

    @override
    def translate_uncached(self, text: str, dst: GameLanguage) -> str:
        src_code: str = googletrans.LANGUAGES["en"]
        dst_code: str = self.get_lang_code(dst)

        return checked_cast(
            googletrans.models.Translated,
            self.__translator.translate(text, dst_code, src_code),
        ).text

    @override
    def mass_translate(self, texts: list[str], dst: GameLanguage) -> dict[str, str]:
        result: dict[str, str] = {}

        src_code: str = googletrans.LANGUAGES["en"]
        dst_code: str = self.get_lang_code(dst)

        to_translate: list[str] = []
        for text in unique(texts):
            cached: Optional[str] = self._get_from_cache(text, dst)
            if cached is not None:
                result[text] = cached
            else:
                to_translate.append(text)

        translated_items: list[googletrans.models.Translated] = cast(
            list[googletrans.models.Translated],
            self.__translator.translate(to_translate, dst_code, src_code),
        )
        for translated_item in translated_items:
            self._add_to_cache(translated_item.origin, translated_item.text, dst)
            result[translated_item.origin] = translated_item.text

        return result

    @staticmethod
    def get_lang_code(language: GameLanguage) -> str:
        """
        Determines the language code to specify in the DeepL API.

        Args:
            language (GameLanguage): The language.

        Returns:
            str: The language code.
        """

        if language in GoogleTranslator.LANG_OVERRIDES:
            return GoogleTranslator.LANG_OVERRIDES[language]

        langcodes: dict[str, str] = cast(dict[str, str], googletrans.LANGCODES)
        return langcodes[language.id]
