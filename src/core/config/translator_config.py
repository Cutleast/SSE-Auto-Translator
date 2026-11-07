"""
Copyright (c) Cutleast
"""

from typing import Annotated, Optional, override

from cutleast_core_lib.core.config.base_config import BaseConfig

from core.translator.apis import TranslatorApi


class TranslatorConfig(BaseConfig):
    """
    Class for translator settings.
    """

    translator: TranslatorApi = TranslatorApi.Google
    """The translator API to use for machine translations."""

    api_key: Annotated[Optional[str], BaseConfig.PropertyMarker.ExcludeFromLogging] = (
        None
    )
    """The API key for the translator API."""

    show_confirmation_dialogs: bool = True
    """Whether to ask for confirmation before starting a machine translation."""

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
