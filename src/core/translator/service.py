"""
Copyright (c) Cutleast
"""

from cutleast_core_lib.core.utilities.singleton import Singleton

from core.config.translator_config import TranslatorConfig

from .apis import TranslatorApi
from .deepl import DeepLTranslator
from .google import GoogleTranslator
from .translator import Translator


class TranslatorService(Singleton):
    """
    Singleton class for providing a translator instance for the current translator
    configuration.
    """

    __translator_config: TranslatorConfig

    def __init__(self, translator_config: TranslatorConfig) -> None:
        """
        Args:
            translator_config (TranslatorConfig): The app-wide translator configuration.
        """

        super().__init__()

        self.__translator_config = translator_config

    def get_translator(self) -> Translator:
        """
        Returns:
            Translator: A translator instance for the current translator configuration.
        """

        translators: dict[TranslatorApi, type[Translator]] = {
            TranslatorApi.Google: GoogleTranslator,
            TranslatorApi.DeepL: DeepLTranslator,
        }

        translator_cls: type[Translator] = translators[
            self.__translator_config.translator
        ]

        return translator_cls(self.__translator_config)
