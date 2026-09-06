"""
Copyright (c) Cutleast
"""

from typing import Any, ClassVar, final, override

import requests
from cutleast_core_lib.core.utilities.hash import sha256_hash

from core.config.translator_config import TranslatorConfig
from core.utilities.game_language import GameLanguage

from .exceptions import (
    GeminiApiKeyMissingError,
    GeminiEmptyTranslationError,
    GeminiNetworkError,
    GeminiPromptMissingError,
    GeminiRequestError,
    GeminiUnexpectedResponseError,
)
from .translator import Translator


@final
class GeminiTranslator(Translator):
    """API class for translating texts with Google Gemini."""

    MODEL: ClassVar[str] = "gemini-2.5-flash"
    """Stable Gemini model used for translations."""

    API_URL: ClassVar[str] = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{MODEL}:generateContent"
    )
    REQUEST_TIMEOUT: ClassVar[int] = 120

    __api_key: str
    __prompt: str

    @override
    def __init__(self, config: TranslatorConfig) -> None:
        super().__init__(config)

        if config.api_key is None or not config.api_key.strip():
            raise GeminiApiKeyMissingError()
        if not config.gemini_prompt.strip():
            raise GeminiPromptMissingError()

        self.__api_key = config.api_key.strip()
        self.__prompt = config.gemini_prompt.strip()

    @override
    def translate_uncached(self, text: str, dst: GameLanguage) -> str:
        """
        Translates a single English text with the Gemini API.

        Args:
            text (str): The English text to translate.
            dst (GameLanguage): The destination language.

        Returns:
            str: The translated text without additional commentary.
        """

        if not text:
            return text

        payload: dict[str, Any] = {
            "systemInstruction": {
                "parts": [
                    {
                        "text": (
                            f"{self.__prompt}\n\nTranslate the user's English text "
                            f"into {dst.value}. Return only the translated text, without "
                            "quotes, labels, explanations, or alternatives."
                        )
                    }
                ]
            },
            "contents": [{"role": "user", "parts": [{"text": text}]}],
            "generationConfig": {
                "candidateCount": 1,
                "temperature": 0.1,
            },
        }

        try:
            response = requests.post(
                GeminiTranslator.API_URL,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.__api_key,
                },
                json=payload,
                timeout=GeminiTranslator.REQUEST_TIMEOUT,
            )
        except requests.RequestException as ex:
            raise GeminiNetworkError() from ex

        try:
            response.raise_for_status()
        except requests.HTTPError as ex:
            message: str = self.__get_error_message(response)
            raise GeminiRequestError(message) from ex

        try:
            data: Any = response.json()
            candidates: Any = data["candidates"]
            parts: Any = candidates[0]["content"]["parts"]
            translated: str = "".join(
                part.get("text", "") for part in parts if isinstance(part, dict)
            ).strip()
        except (KeyError, IndexError, TypeError, ValueError) as ex:
            raise GeminiUnexpectedResponseError() from ex

        if not translated:
            raise GeminiEmptyTranslationError()

        return translated

    @override
    def get_cache_id(self, text: str, dst: GameLanguage) -> str:
        """Includes the model and editable prompt in Gemini cache IDs."""

        data: str = (
            f"{self.__class__.__name__}-{GeminiTranslator.MODEL}-"
            f"{self.__prompt}-{text}-{dst.name}"
        )
        return sha256_hash(data.encode())

    @staticmethod
    def __get_error_message(response: requests.Response) -> str:
        try:
            data: Any = response.json()
            message: Any = data.get("error", {}).get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()
        except TypeError, ValueError:
            pass

        return f"HTTP {response.status_code}"
