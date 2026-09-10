"""
Copyright (c) Cutleast
"""

import pytest
import requests
import requests_mock as requests_mock_module

from core.config.translator_config import TranslatorConfig
from core.translator.exceptions import (
    GeminiApiKeyMissingError,
    GeminiNetworkError,
    GeminiRequestError,
    GeminiUnexpectedResponseError,
)
from core.translator.gemini import GeminiTranslator
from core.utilities.game_language import GameLanguage


class TestGeminiTranslator:
    """Tests `core.translator.gemini.GeminiTranslator`."""

    @staticmethod
    def get_config(api_key: str | None) -> TranslatorConfig:
        """Creates an isolated translator configuration for a test."""

        return TranslatorConfig.model_validate({"api_key": api_key})

    def test_requires_api_key(self) -> None:
        """Tests that the translator requires an API key."""

        with pytest.raises(GeminiApiKeyMissingError):
            GeminiTranslator(self.get_config(None))

    def test_translates_text(self, requests_mock: requests_mock_module.Mocker) -> None:
        """Tests translation and the Gemini request format."""

        # given
        requests_mock.post(
            GeminiTranslator.API_URL,
            json={
                "candidates": [{"content": {"parts": [{"text": "Привет, странник!"}]}}]
            },
        )
        translator = GeminiTranslator(self.get_config("test-api-key"))

        # when
        result: str = translator.translate_uncached(
            "Hello, wanderer!", GameLanguage.Russian
        )

        # then
        assert result == "Привет, странник!"
        assert requests_mock.last_request is not None
        assert requests_mock.last_request.headers["x-goog-api-key"] == "test-api-key"
        request_json = requests_mock.last_request.json()
        assert request_json["contents"][0]["parts"][0]["text"] == "Hello, wanderer!"
        system_instruction: str = request_json["systemInstruction"]["parts"][0]["text"]
        assert "Skyrim" in system_instruction
        assert "Russian" in system_instruction
        assert "ты" in system_instruction
        assert "jarl" in system_instruction
        assert "multiple people" in system_instruction

    def test_uses_custom_prompt(
        self, requests_mock: requests_mock_module.Mocker
    ) -> None:
        """Tests that advanced users can customize the Gemini system prompt."""

        # given
        requests_mock.post(
            GeminiTranslator.API_URL,
            json={"candidates": [{"content": {"parts": [{"text": "Перевод"}]}}]},
        )
        config = self.get_config("test-api-key")
        config.gemini_prompt = "Use the official Russian Skyrim glossary."
        translator = GeminiTranslator(config)

        # when
        translator.translate_uncached("Text", GameLanguage.Russian)

        # then
        assert requests_mock.last_request is not None
        system_instruction: str = requests_mock.last_request.json()["systemInstruction"][
            "parts"
        ][0]["text"]
        assert "official Russian Skyrim glossary" in system_instruction
        assert "Russian" in system_instruction

    def test_reports_api_error(self, requests_mock: requests_mock_module.Mocker) -> None:
        """Tests that a useful Gemini error is raised."""

        # given
        requests_mock.post(
            GeminiTranslator.API_URL,
            status_code=400,
            json={"error": {"message": "API key not valid"}},
        )
        translator = GeminiTranslator(self.get_config("invalid-key"))

        # when / then
        with pytest.raises(GeminiRequestError, match="API key not valid"):
            translator.translate_uncached("Hello", GameLanguage.Russian)

    def test_rejects_redirects(self, requests_mock: requests_mock_module.Mocker) -> None:
        """Tests that redirects cannot forward the API key to another host."""

        # given
        requests_mock.post(
            GeminiTranslator.API_URL,
            status_code=302,
            headers={"Location": "https://example.com"},
        )
        translator = GeminiTranslator(self.get_config("test-api-key"))

        # when / then
        with pytest.raises(GeminiRequestError, match="HTTP 302"):
            translator.translate_uncached("Hello", GameLanguage.Russian)
        assert len(requests_mock.request_history) == 1

    def test_rejects_unexpected_response(
        self, requests_mock: requests_mock_module.Mocker
    ) -> None:
        """Tests that malformed Gemini responses are rejected."""

        # given
        requests_mock.post(GeminiTranslator.API_URL, json={"candidates": []})
        translator = GeminiTranslator(self.get_config("test-api-key"))

        # when / then
        with pytest.raises(GeminiUnexpectedResponseError):
            translator.translate_uncached("Hello", GameLanguage.Russian)

    def test_network_error_is_not_hidden(
        self, requests_mock: requests_mock_module.Mocker
    ) -> None:
        """Tests that connection errors are propagated to the global error handler."""

        # given
        requests_mock.post(
            GeminiTranslator.API_URL,
            exc=requests.ConnectionError("No connection"),
        )
        translator = GeminiTranslator(self.get_config("test-api-key"))

        # when / then
        with pytest.raises(GeminiNetworkError):
            translator.translate_uncached("Hello", GameLanguage.Russian)

    def test_preserves_surrounding_whitespace(
        self, requests_mock: requests_mock_module.Mocker
    ) -> None:
        """Tests that Gemini output whitespace and line breaks are preserved."""

        # given
        translated = " \nПеревод\n "
        requests_mock.post(
            GeminiTranslator.API_URL,
            json={"candidates": [{"content": {"parts": [{"text": translated}]}}]},
        )
        translator = GeminiTranslator(self.get_config("test-api-key"))

        # when / then
        assert (
            translator.translate_uncached("Translation", GameLanguage.Russian)
            == translated
        )

    def test_cache_id_fields_cannot_collide(self) -> None:
        """Tests that ambiguous prompt/text boundaries produce different cache IDs."""

        # given
        first_config = self.get_config("test-api-key")
        first_config.gemini_prompt = "a-b"
        second_config = self.get_config("test-api-key")
        second_config.gemini_prompt = "a"

        # when
        first_id = GeminiTranslator(first_config).get_cache_id("c", GameLanguage.Russian)
        second_id = GeminiTranslator(second_config).get_cache_id(
            "b-c", GameLanguage.Russian
        )

        # then
        assert first_id != second_id
