"""
Copyright (c) Cutleast
"""

import asyncio
from typing import Optional, final, override

import googletrans
import googletrans.models
from cutleast_core_lib.core.utilities.typing_utils import checked_cast
from cutleast_core_lib.core.utilities.unique import unique

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

    @override
    def translate_uncached(self, text: str, dst: GameLanguage) -> str:
        """
        Translates a single text using the Google Translator API.

        Args:
            text (str): The text to translate.
            dst (GameLanguage): The destination language.

        Returns:
            str: The translated text.
        """

        dst_code: str = self.get_lang_code(dst)

        async def _run() -> str:
            async with googletrans.Translator() as translator:
                translated = checked_cast(
                    googletrans.models.Translated,
                    await translator.translate(text, dest=dst_code, src="en"),
                )
                return translated.text

        return asyncio.run(_run())

    @override
    def mass_translate(self, texts: list[str], dst: GameLanguage) -> dict[str, str]:
        """
        Translates multiple texts in a single API call where possible.

        Args:
            texts (list[str]): The texts to translate.
            dst (GameLanguage): The destination language.

        Returns:
            dict[str, str]: Mapping of original text to its translation.
        """

        result: dict[str, str] = {}
        dst_code: str = self.get_lang_code(dst)

        to_translate: list[str] = []
        for text in unique(texts):
            cached: Optional[str] = self._get_from_cache(text, dst)
            if cached is not None:
                result[text] = cached
            else:
                to_translate.append(text)

        if not to_translate:
            return result

        async def _run() -> list[googletrans.models.Translated]:
            async with googletrans.Translator() as translator:
                return await translator.translate(to_translate, dest=dst_code, src="en")

        translated_items: list[googletrans.models.Translated] = asyncio.run(_run())
        for item in translated_items:
            self._add_to_cache(item.origin, item.text, dst)
            result[item.origin] = item.text

        return result

    @staticmethod
    def get_lang_code(language: GameLanguage) -> str:
        """
        Determines the language code to use for the Google Translator API.

        Args:
            language (GameLanguage): The language.

        Returns:
            str: The BCP-47 language code.
        """

        if language in GoogleTranslator.LANG_OVERRIDES:
            return GoogleTranslator.LANG_OVERRIDES[language]

        return googletrans.LANGCODES[language.id]
