"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import googletrans
import qtpy.QtWidgets as qtw

from main import MainApp

from .translator import Translator


class GoogleTranslator(Translator):
    """
    Class for Google Translator.
    """

    name = "Google Translator"

    cache: dict[str, str] = {}

    langs = {
        "chinese": "zh-cn",
        "portuguese": "pt-br",
    }

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.translator = googletrans.Translator()

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

    def get_settings_widget(self):
        return qtw.QLabel(self.app.loc.settings.no_config_required)
