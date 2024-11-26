"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from PySide6.QtWidgets import QWidget

from app import MainApp


class Translator:
    """
    Base class for all Translator APIs.
    """

    name: str = None

    def __init__(self, app: MainApp):
        self.app = app

    def translate(self, text: str, src: str, dst: str) -> str:
        """
        Translates `text` from `src` language to `dst` language.
        """

        raise NotImplementedError

    def mass_translate(self, texts: list[str], src: str, dst: str) -> dict[str, str]:
        """
        Translates `texts` and returns translated result with original texts as keys.
        """

        raise NotImplementedError

    def get_settings_widget(self) -> QWidget:
        """
        Returns settings widget for configuring translator API.
        """

        raise NotImplementedError
