"""
Copyright (c) Cutleast
"""

from enum import Enum

from .translator import Translator


class TranslatorApi(Enum):
    """Enum for available translator APIs."""

    Google = "Google Translator"
    """Google translator API (free)."""

    DeepL = "DeepL"
    """DeepL translator API (requires API key)."""

    def get_api_class(self) -> type[Translator]:
        """
        Returns the API class for this API.

        Returns:
            type[Translator]: The API class.
        """

        from .deepl import DeepLTranslator
        from .google import GoogleTranslator

        apis: dict[TranslatorApi, type[Translator]] = {
            TranslatorApi.Google: GoogleTranslator,
            TranslatorApi.DeepL: DeepLTranslator,
        }

        return apis[self]
