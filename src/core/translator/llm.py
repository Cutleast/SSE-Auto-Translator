"""
Copyright (c) Cutleast
"""

import re
from typing import Optional, final, override

from cutleast_core_lib.core.utilities.localized_enum import LocalizedEnum
from openai import APIConnectionError, BadRequestError
from openai import OpenAI as OpenAIClient
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
from openai.types.chat.chat_completion import Choice

from core.config.translator_config import TranslatorConfig
from core.mod_file.context import ModFileContext
from core.translation_context.glossary import TranslationGlossary
from core.translation_context.similar import SimilarString

from .exceptions import LlmConnectionError, LlmReplyCutOffError
from .models import TranslationRequest
from .translator import Translator
from .utils import format_pair, format_string


@final
class LlmTranslator(Translator):
    """
    Translator API for OpenAI-compatible LLM providers.
    """

    class ProviderPreset(str, LocalizedEnum):
        """
        Enum for the known LLM provider and their corresponding base URLs.
        """

        LmStudio = "http://127.0.0.1:1234/v1"
        Ollama = "http://127.0.0.1:11434/v1"
        OpenAi = "https://api.openai.com/v1"
        Gemini = "https://generativelanguage.googleapis.com/v1beta/openai/"
        Anthropic = "https://api.anthropic.com/v1/"
        OpenRouter = "https://openrouter.ai/api/v1"

        @override
        def get_localized_name(self) -> str:
            match self:
                case LlmTranslator.ProviderPreset.LmStudio:
                    return "LM Studio"
                case LlmTranslator.ProviderPreset.Ollama:
                    return "Ollama"
                case LlmTranslator.ProviderPreset.OpenAi:
                    return "OpenAI"
                case LlmTranslator.ProviderPreset.Gemini:
                    return "Google Gemini"
                case LlmTranslator.ProviderPreset.Anthropic:
                    return "Anthropic"
                case LlmTranslator.ProviderPreset.OpenRouter:
                    return "OpenRouter"

    LANGUAGE_PLACEHOLDER: str = "{language}"
    """Placeholder in the system prompt that is replaced with the target language."""

    TEXT_HEADING: str = "Text to translate:"
    """The heading that precedes the text to translate in the user prompt."""

    UNCHANGED_MARKER: str = "(keep unchanged)"
    """Marker for glossary terms whose official translation equals their original."""

    INSTRUCTIONS_HEADING: str = "Instructions of the user for this translation:"
    """The heading that precedes additional instructions of the user."""

    MAX_RELATED_STRINGS: int = 10
    """Maximum number of related strings included in the user prompt."""

    MAX_CONTEXT_STRING_LENGTH: int = 300
    """Maximum length of strings included in the context. Longer ones are truncated."""

    REASONING_PATTERN: re.Pattern[str] = re.compile(
        r"<think>.*?</think>", re.DOTALL | re.IGNORECASE
    )
    """Pattern for reasoning blocks that some models prepend to their answer."""

    LIST_MODELS_TIMEOUT: float = 5.0
    """Timeout in seconds for requesting the available models."""

    __client: OpenAIClient
    __model: str
    __temperature: Optional[float]
    __system_prompt: str

    @override
    def __init__(self, config: TranslatorConfig) -> None:
        super().__init__(config)

        if not config.llm_base_url is not None:
            raise RuntimeError("LLM base URL is required!")

        if not config.llm_model:
            raise RuntimeError("LLM model is required!")

        self.__client = OpenAIClient(
            base_url=config.llm_base_url, api_key=config.llm_api_key or "none"
        )
        self.__model = config.llm_model
        self.__temperature = config.llm_temperature
        self.__system_prompt = config.llm_system_prompt

    @override
    def _process_request(self, request: TranslationRequest) -> str:
        prompt: list[ChatCompletionMessageParam] = self.__build_prompt(request)

        try:
            return self.__process_completion(
                self.__client.chat.completions.create(
                    model=self.__model, messages=prompt, temperature=self.__temperature
                )
            )

        except BadRequestError as ex:
            if "temperature" not in str(ex).lower() or self.__temperature is None:
                raise

            self.log.warning(
                f"Model '{self.__model}' rejected the temperature "
                f"'{self.__temperature}'. Retrying with the server's default "
                "temperature..."
            )
            self.__temperature = None
            return self._process_request(request)

        except APIConnectionError as ex:
            raise LlmConnectionError from ex

    def __process_completion(self, completion: ChatCompletion) -> str:
        if not completion.choices:
            raise RuntimeError(f"Model '{self.__model}' returned no translation.")

        choice: Choice = completion.choices[0]
        if choice.finish_reason == "length":
            raise LlmReplyCutOffError

        translation: str = LlmTranslator.REASONING_PATTERN.sub(
            "", choice.message.content or ""
        ).strip()
        if not translation:
            raise RuntimeError(f"Model '{self.__model}' returned no translation.")

        return translation

    def __build_prompt(
        self, request: TranslationRequest
    ) -> list[ChatCompletionMessageParam]:
        """
        Builds the entire system and user prompt for a translation request.

        Args:
            request (TranslationRequest): The translation request.

        Returns:
            list[ChatCompletionMessageParam]:
                The system and user prompt for the translation request.
        """

        system_prompt: str = self.__system_prompt.replace(
            LlmTranslator.LANGUAGE_PLACEHOLDER, request.dst.name
        )

        user_prompt: str = "\n\n".join(
            [
                LlmTranslator.__build_mod_file_context_section(
                    request.context.mod_file_context
                ),
                LlmTranslator.__build_similar_section(request.context.similar_strings),
                LlmTranslator.__build_glossary_section(request.context.glossary_terms),
                f"{LlmTranslator.TEXT_HEADING}\n{request.text}",
            ]
        )

        if request.instructions is not None:
            user_prompt += "\n\nAdditional instructions: "
            user_prompt += request.instructions

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    @staticmethod
    def __build_mod_file_context_section(mod_file_context: ModFileContext) -> str:
        """
        Builds the prompt section for the mod file-specific context of a string.

        Args:
            mod_file_context (ModFileContext): The mod file-specific context.

        Returns:
            str: The prompt section.
        """

        lines: list[str] = []

        if mod_file_context.string_kind is not None:
            lines.append(f"String kind: {mod_file_context.string_kind}")

        for property in mod_file_context.properties:
            lines.append(f"{property.label}: {property.value}")

        if mod_file_context.notes:
            lines.append("Notes:")
            for note in mod_file_context.notes:
                lines.append(f"- {note}")

        if mod_file_context.related_strings:
            lines.append("Related strings:")

            for related_string in mod_file_context.related_strings[
                : LlmTranslator.MAX_RELATED_STRINGS
            ]:
                line: str = f"- {related_string.relation}: "
                line += format_pair(
                    related_string.string.original,
                    related_string.string.string,
                    LlmTranslator.MAX_CONTEXT_STRING_LENGTH,
                )
                lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def __build_similar_section(similar_strings: list[SimilarString]) -> str:
        """
        Builds the prompt section for the similar strings of a translation request.

        Args:
            similar_strings (list[SimilarString]):
                The similar strings to include in the prompt.

        Returns:
            str: The prompt section.
        """

        if not similar_strings:
            return ""

        lines: list[str] = ["Existing translations of similar strings:"]
        for similar_string in similar_strings:
            line: str = "- "
            line += format_pair(
                similar_string.string.original,
                similar_string.string.string,
                LlmTranslator.MAX_CONTEXT_STRING_LENGTH,
            )
            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def __build_glossary_section(
        glossary_terms: list[TranslationGlossary.Term],
    ) -> str:
        """
        Builds the prompt section for the glossary terms of a translation request.

        Args:
            glossary_terms (list[TranslationGlossary.Term]):
                The glossary terms to include in the prompt.

        Returns:
            str: The prompt section.
        """

        if not glossary_terms:
            return ""

        lines: list[str] = ["Glossary:"]
        for term in glossary_terms:
            line: str = "- "
            if term.translated == term.original:
                line += format_string(
                    term.original, LlmTranslator.MAX_CONTEXT_STRING_LENGTH
                )
                line += " "
                line += LlmTranslator.UNCHANGED_MARKER
            else:
                line += format_pair(
                    term.original,
                    term.translated,
                    LlmTranslator.MAX_CONTEXT_STRING_LENGTH,
                )

            if term.example is not None:
                line += " (Example: "
                line += format_pair(
                    term.example.original,
                    term.example.translated,
                    LlmTranslator.MAX_CONTEXT_STRING_LENGTH,
                )
                line += ")"

            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def list_models(
        base_url: str, api_key: Optional[str], timeout: float = LIST_MODELS_TIMEOUT
    ) -> list[str]:
        """
        Requests the names of the models that are available at an OpenAI-compatible API.

        Args:
            base_url (str): The base URL of the API.
            api_key (Optional[str]): The API key or None if the API requires none.
            timeout (float, optional):
                The timeout for the request in seconds. Defaults to 5.

        Raises:
            OpenAIError:
                If the request failed, for eg. because the server is not reachable.

        Returns:
            list[str]: The sorted names of the available models.
        """

        try:
            client = OpenAIClient(
                base_url=base_url.strip(),
                api_key=api_key or "none",
                timeout=timeout,
                max_retries=0,
            )

            return sorted({model.id for model in client.models.list(timeout=timeout)})
        except APIConnectionError as ex:
            raise LlmConnectionError from ex

    @classmethod
    @override
    def supports_parallel_requests(cls) -> bool:
        return True

    @classmethod
    @override
    def supports_corrections(cls) -> bool:
        return True

    @classmethod
    @override
    def supports_instructions(cls) -> bool:
        return True
