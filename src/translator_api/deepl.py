"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import deepl
import googletrans

from .translator import Translator
from main import MainApp


class DeepLTranslator(Translator):
    """
    Class for DeepL API (requires API key).
    """

    name = "DeepL"

    cache: dict[str, str] = {}

    def __init__(self, app: MainApp):
        super().__init__(app)

        # Todo: load config from app
        self.api_key = app.translator_config["api_key"]

        self.translator = deepl.Translator(self.api_key)

        # Load glossary
        self.glossary_id: str = None

        if self.glossary_id is not None:
            self.glossary = self.translator.get_glossary(self.glossary_id)
        else:
            self.glossary = None

    def translate(self, text: str, src: str, dst: str) -> str:
        if text not in self.cache:
            src_code = googletrans.LANGCODES[src.lower()]
            dst_code = googletrans.LANGCODES[dst.lower()]

            if self.glossary is not None:
                result: deepl.TextResult = self.translator.translate_text_with_glossary(
                    text, self.glossary, dst_code
                )

            else:
                result: deepl.TextResult = self.translator.translate_text(
                    text, source_lang=src_code, target_lang=dst_code
                )
            
            self.cache[text] = result.text

        return self.cache
