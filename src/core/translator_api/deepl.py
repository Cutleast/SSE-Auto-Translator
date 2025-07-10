"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from typing import Optional, override

import deepl
import googletrans

from core.config.translator_config import TranslatorConfig

from .translator import Translator
from .translator_api import TranslatorApi


class DeepLTranslator(Translator):
    """
    Class for DeepL API (requires API key).
    """

    name = TranslatorApi.DeepL.value

    cache: dict[str, str] = {}

    langs = {
        "portuguese": "PT-BR",
        "chinese": "ZH",
    }

    glossary_id: Optional[str]
    glossary: Optional[deepl.GlossaryInfo]

    def __init__(self, translator_config: TranslatorConfig) -> None:
        super().__init__(translator_config)

        if self.translator_config.api_key is None:
            raise ValueError("DeepL API key is required")

        self.translator = deepl.Translator(self.translator_config.api_key)

        # TODO: Load glossary from user config
        self.glossary_id = None

        if self.glossary_id is not None:
            self.glossary = self.translator.get_glossary(self.glossary_id)
        else:
            self.glossary = None

    @override
    def mass_translate(self, texts: list[str], src: str, dst: str) -> dict[str, str]:
        result: dict[str, str] = {}

        texts = list(set(texts))  # Remove duplicates

        # This can't be further optimized because DeepL charges
        # per translated characters not per requests
        for text in texts:
            result[text] = self.translate(text, src, dst)

        return result

    @override
    def translate(self, text: str, src: str, dst: str) -> str:
        if text not in self.cache:
            # Get language codes from DeepLTranslator.langs
            # and googletrans.LANGCODES as fallback
            src_code = self.langs.get(
                src.lower(),
                googletrans.LANGCODES.get(src.lower(), src),  # type: ignore
            )
            dst_code = self.langs.get(
                dst.lower(),
                googletrans.LANGCODES.get(dst.lower(), dst),  # type: ignore
            )

            result: deepl.TextResult
            if self.glossary is not None:
                result = self.translator.translate_text_with_glossary(  # type: ignore[assignment]
                    text, self.glossary, dst_code
                )

            else:
                result = self.translator.translate_text(
                    text,
                    source_lang=src_code,
                    target_lang=dst_code,  # type: ignore
                )

            self.cache[text] = result.text

        return self.cache[text]
