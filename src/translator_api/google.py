"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import qtpy.QtWidgets as qtw
import googletrans

from main import MainApp

from .translator import Translator


class GoogleTranslator(Translator):
    """
    Class for Google Translator.
    """

    name = "Google Translator"

    cache: dict[str, str] = {}

    def __init__(self, app: MainApp):
        super().__init__(app)

        self.translator = googletrans.Translator()

    def translate(self, text: str, src: str, dst: str) -> str:
        if text not in self.cache:
            self.cache[text] = self.translator.translate(
            text, googletrans.LANGCODES[dst.lower()], googletrans.LANGCODES[src.lower()]
        ).text

        return self.cache[text]

    def get_settings_widget(self):
        return qtw.QLabel(self.app.loc.settings.no_config_required)
