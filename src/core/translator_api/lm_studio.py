"""
Copyright (c) Cutleast
"""

from json import JSONDecodeError, dumps, loads
from typing import Any, Optional, cast, override
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from core.config.translator_config import TranslatorConfig

from .translator import Translator
from .translator_api import TranslatorApi


class LMStudioTranslator(Translator):
    """
    Translator implementation for the LM Studio local OpenAI-compatible API.
    """

    name = TranslatorApi.LMStudio.value

    cache: dict[str, str] = {}

    def __init__(self, translator_config: TranslatorConfig) -> None:
        super().__init__(translator_config)

        self.base_url = self.normalize_base_url(translator_config.lm_studio_base_url)
        if not self.base_url:
            raise ValueError("LM Studio base URL is required")

        self.model = translator_config.lm_studio_model
        self.use_server_prompt = translator_config.lm_studio_use_server_prompt

    @override
    def translate(self, text: str, src: str, dst: str) -> str:
        if text not in self.cache:
            model = self.__get_model()
            self.cache[text] = self.__translate_text(text, src, dst, model)

        return self.cache[text]

    @override
    def mass_translate(self, texts: list[str], src: str, dst: str) -> dict[str, str]:
        result: dict[str, str] = {}
        texts = list(set(texts))
        to_translate = [text for text in texts if text not in self.cache]

        if to_translate:
            model = self.__get_model()
            for text in to_translate:
                self.cache[text] = self.__translate_text(text, src, dst, model)

        for text in texts:
            result[text] = self.cache[text]

        return result

    def __translate_text(self, text: str, src: str, dst: str, model: str) -> str:
        messages = [
            {
                "role": "user",
                "content": self.__build_user_prompt(text, src, dst),
            }
        ]

        if not self.use_server_prompt:
            messages.insert(
                0,
                {
                    "role": "system",
                    "content": self.__build_system_prompt(src, dst),
                },
            )

        payload = {
            "model": model,
            "temperature": 0.2,
            "messages": messages,
        }

        data = self.request_json(
            self.base_url,
            "/v1/chat/completions",
            method="POST",
            payload=payload,
        )
        choices = cast(list[dict[str, Any]], data.get("choices", []))
        if not choices:
            raise ValueError("LM Studio returned no completion choices")

        message = cast(dict[str, Any], choices[0].get("message", {}))
        content = cast(Optional[str], message.get("content"))
        if content is None:
            raise ValueError("LM Studio returned an empty response")

        return content.strip()

    @staticmethod
    def __build_system_prompt(src: str, dst: str) -> str:
        return (
            "Translate game localisation strings from "
            f"{src} to {dst}. Return only the translated text. "
            "Preserve placeholders, markup, special characters, "
            "escape sequences, punctuation and line breaks exactly. "
            "Do not explain anything."
        )

    @staticmethod
    def __build_user_prompt(text: str, src: str, dst: str) -> str:
        return (
            f"Source language: {src}\n"
            f"Target language: {dst}\n"
            "Translate the following game localisation text. Return only the translated text. "
            "Preserve placeholders, markup, special characters, escape sequences, punctuation and line breaks exactly.\n\n"
            f"{text}"
        )

    def __get_model(self) -> str:
        if self.model:
            return self.model

        models = self.list_models(self.base_url)
        if not models:
            raise ValueError(
                "No LM Studio model available. Load a model in LM Studio or configure one explicitly."
            )

        model = models[0]
        self.model = model
        return model

    @staticmethod
    def normalize_base_url(base_url: str) -> str:
        return base_url.strip().rstrip("/")

    @classmethod
    def list_models(cls, base_url: str) -> list[str]:
        data = cls.request_json(cls.normalize_base_url(base_url), "/v1/models")
        models = cast(list[dict[str, Any]], data.get("data", []))

        result: list[str] = []
        for model_entry in models:
            model = cast(Optional[str], model_entry.get("id"))
            if model:
                result.append(model)

        return result

    @staticmethod
    def request_json(
        base_url: str,
        path: str,
        method: str = "GET",
        payload: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        body = dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            url=f"{base_url}{path}",
            data=body,
            headers=headers,
            method=method,
        )

        try:
            with urlopen(request, timeout=60) as response:
                response_text = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ConnectionError(
                f"LM Studio request failed with HTTP {exc.code}: {detail}"
            ) from exc
        except URLError as exc:
            raise ConnectionError(
                "Could not reach LM Studio. Make sure the local server is running."
            ) from exc

        try:
            data = loads(response_text)
        except JSONDecodeError as exc:
            raise ValueError("LM Studio returned invalid JSON") from exc

        if not isinstance(data, dict):
            raise ValueError("LM Studio returned an unexpected response")

        return cast(dict[str, Any], data)