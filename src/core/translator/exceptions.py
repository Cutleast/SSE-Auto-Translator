"""
Copyright (c) Cutleast
"""

from typing import override

from PySide6.QtWidgets import QApplication

from core.utilities.exceptions import LocalizedException


class GeminiError(LocalizedException):
    """Base class for Gemini translator errors."""

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Gemini translation failed!")


class GeminiApiKeyMissingError(GeminiError):
    """Exception raised when no Gemini API key is configured."""

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Gemini API key is required!")


class GeminiPromptMissingError(GeminiError):
    """Exception raised when no Gemini system prompt is configured."""

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Gemini system prompt is required!")


class GeminiRequestError(GeminiError):
    """Exception raised when the Gemini API rejects a request."""

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Gemini API request failed: {0}")


class GeminiNetworkError(GeminiError):
    """Exception raised when the Gemini API cannot be reached."""

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate("exceptions", "Could not reach the Gemini API.")


class GeminiUnexpectedResponseError(GeminiError):
    """Exception raised when the Gemini response cannot be parsed."""

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions", "Gemini API returned an unexpected response."
        )


class GeminiEmptyTranslationError(GeminiError):
    """Exception raised when Gemini returns an empty translation."""

    @override
    def getLocalizedMessage(self) -> str:
        return QApplication.translate(
            "exceptions", "Gemini API returned an empty translation."
        )
