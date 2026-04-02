from typing import Any

from core.config.translator_config import TranslatorConfig
from core.translator_api.lm_studio import LMStudioTranslator


class TestLMStudioTranslator:
    def test_translate_uses_lm_studio_server_prompt(self, monkeypatch) -> None:
        payloads: list[dict[str, Any]] = []

        def request_json(
            base_url: str,
            path: str,
            method: str = "GET",
            payload: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            assert base_url == "http://127.0.0.1:1234"
            assert path == "/v1/chat/completions"
            assert method == "POST"
            payloads.append(payload or {})
            return {"choices": [{"message": {"content": "Hallo"}}]}

        monkeypatch.setattr(LMStudioTranslator, "request_json", staticmethod(request_json))

        config = TranslatorConfig()
        config.lm_studio_model = "qwen-3-8b"
        config.lm_studio_use_server_prompt = True

        LMStudioTranslator.cache = {}
        translator = LMStudioTranslator(config)

        result = translator.translate("Hello", "English", "German")

        assert result == "Hallo"
        assert len(payloads) == 1
        assert payloads[0]["messages"] == [
            {
                "role": "user",
                "content": (
                    "Source language: English\n"
                    "Target language: German\n"
                    "Translate the following game localisation text. Return only the translated text. "
                    "Preserve placeholders, markup, special characters, escape sequences, punctuation and line breaks exactly.\n\n"
                    "Hello"
                ),
            }
        ]

    def test_translate_uses_internal_system_prompt(self, monkeypatch) -> None:
        payloads: list[dict[str, Any]] = []

        def request_json(
            base_url: str,
            path: str,
            method: str = "GET",
            payload: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            payloads.append(payload or {})
            return {"choices": [{"message": {"content": "Hallo"}}]}

        monkeypatch.setattr(LMStudioTranslator, "request_json", staticmethod(request_json))

        config = TranslatorConfig()
        config.lm_studio_model = "qwen-3-8b"
        config.lm_studio_use_server_prompt = False

        LMStudioTranslator.cache = {}
        translator = LMStudioTranslator(config)

        translator.translate("Hello", "English", "German")

        assert payloads[0]["messages"][0] == {
            "role": "system",
            "content": (
                "Translate game localisation strings from English to German. "
                "Return only the translated text. Preserve placeholders, markup, special characters, "
                "escape sequences, punctuation and line breaks exactly. Do not explain anything."
            ),
        }
        assert payloads[0]["messages"][1]["role"] == "user"