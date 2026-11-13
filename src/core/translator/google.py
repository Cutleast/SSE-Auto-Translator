"""
Copyright (c) Cutleast
"""

import asyncio
from typing import ClassVar, final, override

import googletrans
import googletrans.models
from cutleast_core_lib.core.utilities.typing_utils import checked_cast

from core.config.translator_config import TranslatorConfig
from core.translator.models.request import TranslationRequest
from core.utilities.game_language import GameLanguage

from .translator import Translator


@final
class GoogleTranslator(Translator):
    """
    API class for translating texts with Google Translator.
    """

    LANG_OVERRIDES: ClassVar[dict[GameLanguage, str]] = {
        GameLanguage.Chinese: "zh-cn",
        GameLanguage.Portuguese: "pt",
    }

    __translator: googletrans.Translator

    @override
    def __init__(self, config: TranslatorConfig) -> None:
        super().__init__(config)

        self.__translator = googletrans.Translator()

    @override
    def _process_request(self, request: TranslationRequest) -> str:
        dst_code: str = self.get_lang_code(request.dst)

        async def _run() -> str:
            translated = checked_cast(
                googletrans.models.Translated,
                await self.__translator.translate(request.text, dest=dst_code, src="en"),
            )
            return translated.text

        return asyncio.run(_run())

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
