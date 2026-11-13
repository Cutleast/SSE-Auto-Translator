"""
Copyright (c) Cutleast
"""

from typing import Annotated, Optional, override

from cutleast_core_lib.core.config.base_config import BaseConfig
from pydantic import Field

from core.translator.apis import TranslatorApi


class TranslatorConfig(BaseConfig):
    """
    Class for translator settings.
    """

    translator: TranslatorApi = TranslatorApi.Google
    """The translator API to use for machine translations."""

    deepl_api_key: Annotated[
        Optional[str],
        BaseConfig.PropertyMarker.ExcludeFromLogging,
        Field(alias="api_key"),
    ] = None
    """The API key for the DeepL API."""

    show_confirmation_dialogs: bool = True
    """Whether to ask for confirmation before starting a machine translation."""

    max_parallel_requests: Annotated[int, Field(ge=1, le=32)] = 4
    """
    The maximum number of requests sent to the translator in parallel, if supported by
    the selected translator.
    """

    glossary: dict[str, str] = Field(default_factory=dict[str, str])
    """
    Custom translations of terms for the translator by their original, for eg.
    "hold" -> "Fürstentum". They take precedence over terms from the base game or other
    translations.
    """

    llm_base_url: Optional[str] = None
    """The base URL for the LLM provider."""

    llm_api_key: Optional[str] = None
    """The API key for the LLM provider."""

    llm_model: Optional[str] = None
    """The model to use for LLM translations."""

    llm_temperature: Optional[float] = 0.2
    """The temperature for the LLM inference."""

    llm_system_prompt: str = """\
You are an expert translator localizing mods for the video game The Elder Scrolls V: \
Skyrim from English into {language}.

Rules:
- Translate only the text after "Text to translate:" and output nothing but the \
translation: no comments, explanations, quotes or markdown.
- Keep placeholders, markup, tags and line breaks exactly as in the original.
- Use the provided context to choose the correct meaning, grammatical form and tone, \
but never translate the context itself.
- Use the glossary translations as reference for the listed terms and adapt them \
grammatically where necessary.
- Follow the terminology of the existing translations of similar strings to stay \
consistent with the game.
- Translate names and lore terms as in the official {language} version of Skyrim.
- Use the language of a medieval fantasy world: avoid modern words and anglicisms.
- Write correct {language} without invented words and with correct grammar and spelling.
- Additional instructions by the user **always** take precedence over the rules listed \
here.\
"""
    """The system prompt for the LLM translator API."""

    @override
    @staticmethod
    def get_config_name() -> str:
        return "translator/config.json"
