"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

from abc import abstractmethod

from PySide6.QtCore import QObject

from core.config.translator_config import TranslatorConfig


class Translator(QObject):
    """
    Base class for all Translator APIs.
    """

    name: str
    translator_config: "TranslatorConfig"

    def __init__(self, translator_config: TranslatorConfig) -> None:
        super().__init__()

        self.translator_config = translator_config

    @abstractmethod
    def translate(self, text: str, src: str, dst: str) -> str:
        """
        Translates `text` from `src` language to `dst` language.
        """

    @abstractmethod
    def mass_translate(self, texts: list[str], src: str, dst: str) -> dict[str, str]:
        """
        Translates `texts` and returns translated result with original texts as keys.
        """


if __name__ == "__main__":
    from core.config.translator_config import TranslatorConfig
