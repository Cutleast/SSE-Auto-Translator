"""
Copyright (c) Cutleast
"""

from typing import final, override

import deepl
from cutleast_core_lib.core.utilities.typing_utils import checked_cast

from core.config.translator_config import TranslatorConfig
from core.utilities.game_language import GameLanguage

from .translator import Translator


@final
class DeepLTranslator(Translator):
    """
    API class for translating texts with DeepL.
    """

    LANG_OVERRIDES: dict[GameLanguage, str] = {
        GameLanguage.Portuguese: deepl.Language.PORTUGUESE_BRAZILIAN,
        GameLanguage.Chinese: deepl.Language.CHINESE,
    }

    __translator: deepl.Translator

    @override
    def __init__(self, config: TranslatorConfig) -> None:
        super().__init__(config)

        if config.api_key is None:
            raise RuntimeError("DeepL API key is required!")

        self.__translator = deepl.Translator(config.api_key)

    @override
    def translate_uncached(self, text: str, dst: GameLanguage) -> str:
        src_code: str = deepl.Language.ENGLISH
        dst_code: str = self.get_lang_code(dst)

        return checked_cast(
            deepl.TextResult,
            self.__translator.translate_text(
                text, source_lang=src_code, target_lang=dst_code
            ),
        ).text

    @staticmethod
    def get_lang_code(language: GameLanguage) -> str:
        """
        Determines the language code to specify in the DeepL API.

        Args:
            language (GameLanguage): The language.

        Returns:
            str: The language code.
        """

        if language in DeepLTranslator.LANG_OVERRIDES:
            return DeepLTranslator.LANG_OVERRIDES[language]

        return checked_cast(str, getattr(deepl.Language, language.name.upper()))
