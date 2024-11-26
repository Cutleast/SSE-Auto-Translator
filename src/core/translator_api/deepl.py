"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import deepl
import googletrans

from app import MainApp

from .translator import Translator


class DeepLTranslator(Translator):
    """
    Class for DeepL API (requires API key).
    """

    name = "DeepL"

    cache: dict[str, str] = {}

    langs = {
        "portuguese": "PT-BR",
        "chinese": "ZH",
    }

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.api_key = app.translator_config["api_key"]

        self.translator = deepl.Translator(self.api_key)

        # Todo: Load glossary from user config
        self.glossary_id: str = None

        if self.glossary_id is not None:
            self.glossary = self.translator.get_glossary(self.glossary_id)
        else:
            self.glossary = None

    def mass_translate(self, texts: list[str], src: str, dst: str) -> dict[str, str]:
        result: dict[str, str] = {}

        texts = list(set(texts))  # Remove duplicates

        # This can't be further optimized because DeepL charges
        # per translated characters not per requests
        for text in texts:
            result[text] = self.translate(text, src, dst)

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

            if self.glossary is not None:
                result: deepl.TextResult = self.translator.translate_text_with_glossary(
                    text, self.glossary, dst_code
                )

            else:
                result: deepl.TextResult = self.translator.translate_text(
                    text, source_lang=src_code, target_lang=dst_code
                )

            self.cache[text] = result.text

        return self.cache[text]
