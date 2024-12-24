"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import googletrans
from googletrans.client import Translated

from .translator import Translator


class GoogleTranslator(Translator):
    """
    Class for Google Translator.
    """

    name = "Google Translator"

    cache: dict[str, str] = {}

    langs = {
        "chinese": "zh-cn",
    }

    def __init__(self) -> None:
        super().__init__()

        self.translator = googletrans.Translator()

    def mass_translate(self, texts: list[str], src: str, dst: str) -> dict[str, str]:
        # Get language codes from DeepLTranslator.langs
        # and googletrans.LANGCODES as fallback
        src_code = self.langs.get(
            src.lower(), googletrans.LANGCODES.get(src.lower(), src)
        )
        dst_code = self.langs.get(
            dst.lower(), googletrans.LANGCODES.get(dst.lower(), dst)
        )

        result: dict[str, str] = {}

        texts = list(set(texts))  # Remove duplicates

        # Translate texts that are not already in cache
        to_translate: list[str] = [text for text in texts if text not in self.cache]

        translated_items: list[Translated] = self.translator.translate(
            to_translate, dst_code, src_code
        )

        for translated_item in translated_items:
            self.cache[translated_item.origin] = translated_item.text

        # Get translated texts from cache
        for text in texts:
            result[text] = self.cache[text]

        return result

    def translate(self, text: str, src: str, dst: str) -> str:
        if text not in self.cache:
            # Get language codes from DeepLTranslator.langs
            # and googletrans.LANGCODES as fallback
            src_code = self.langs.get(
                src.lower(), googletrans.LANGCODES.get(src.lower(), src)
            )
            dst_code = self.langs.get(
                dst.lower(), googletrans.LANGCODES.get(dst.lower(), dst)
            )

            self.cache[text] = self.translator.translate(text, dst_code, src_code).text

        return self.cache[text]
