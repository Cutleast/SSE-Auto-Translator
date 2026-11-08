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

    @override
    @staticmethod
    def get_config_name() -> str:
        return "translator/config.json"
