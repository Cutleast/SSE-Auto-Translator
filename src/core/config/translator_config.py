"""
Copyright (c) Cutleast
"""

from typing import Annotated, Optional, override

from cutleast_core_lib.core.config.base_config import BaseConfig

from core.translator_api.translator_api import TranslatorApi


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

    lm_studio_base_url: str = "http://127.0.0.1:1234"
    """Base URL of the LM Studio local server."""

    lm_studio_model: Optional[str] = None
    """Model name for LM Studio. If unset, the first loaded model is used."""

    lm_studio_use_server_prompt: bool = True
    """Whether to use the prompt configured in LM Studio instead of SSE-AT's built-in system prompt."""

    show_confirmation_dialogs: bool = True
    """Whether to ask for confirmation before starting a machine translation."""

    @override
    @staticmethod
    def get_config_name() -> str:
        return "translator/config.json"
