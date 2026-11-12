"""
Copyright (c) Cutleast
"""

import logging

from cutleast_core_lib.core.config.manager import ConfigManager
from cutleast_core_lib.core.utilities.singleton import Singleton
from PySide6.QtCore import QObject

from core.config.translator_config import TranslatorConfig

from .apis import TranslatorApi
from .deepl import DeepLTranslator
from .google import GoogleTranslator
from .llm import LlmTranslator
from .translator import Translator


# must be a QObject to be able to connect to signals, wtf?
class TranslatorService(QObject, Singleton):
    """
    Singleton class for providing a translator instance for the current translator
    configuration.
    """

    _CLASSES: dict[TranslatorApi, type[Translator]] = {
        TranslatorApi.Google: GoogleTranslator,
        TranslatorApi.DeepL: DeepLTranslator,
        TranslatorApi.Llm: LlmTranslator,
    }

    __translator_config: TranslatorConfig
    __translator: Translator

    log: logging.Logger = logging.getLogger("TranslatorService")

    def __init__(
        self, translator_config_manager: ConfigManager[TranslatorConfig]
    ) -> None:
        """
        Args:
            translator_config_manager (ConfigManager[TranslatorConfig]):
                The manager for the translator configuration.
        """

        super().__init__()
        Singleton.__init__(self)

        self.__translator_config = translator_config_manager.config
        self.__update_translator()

        translator_config_manager.saved.connect(self.__update_translator)

    def __update_translator(self) -> None:
        translator_cls: type[Translator] = TranslatorService._CLASSES[
            self.__translator_config.translator
        ]

        self.__translator = translator_cls(self.__translator_config)

        self.log.debug("Translator updated for translator configuration.")

    def get_translator(self) -> Translator:
        """
        Returns:
            Translator: A translator instance for the current translator configuration.
        """

        return self.__translator
