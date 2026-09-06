"""
Copyright (c) Cutleast
"""

from typing import Annotated, ClassVar, Optional, override

from cutleast_core_lib.core.config.base_config import BaseConfig

from core.translator.apis import TranslatorApi


class TranslatorConfig(BaseConfig):
    """
    Class for translator settings.
    """

    DEFAULT_GEMINI_PROMPT: ClassVar[str] = (
        "You are a professional localization translator for The Elder Scrolls V: "
        "Skyrim and Skyrim mods. Use established Skyrim and The Elder Scrolls "
        "terminology, lore, names, and the appropriate in-game style. Preserve line "
        "breaks, formatting, placeholders, markup, and control sequences exactly."
    )
    """Default system prompt used for Gemini translations."""

    translator: TranslatorApi = TranslatorApi.Google
    """The translator API to use for machine translations."""

    api_key: Annotated[Optional[str], BaseConfig.PropertyMarker.ExcludeFromLogging] = (
        None
    )
    """The API key for the translator API."""

    gemini_prompt: str = DEFAULT_GEMINI_PROMPT
    """The editable system prompt used to give Gemini localization context."""

    show_confirmation_dialogs: bool = True
    """Whether to ask for confirmation before starting a machine translation."""

    @override
    @staticmethod
    def get_config_name() -> str:
        return "translator/config.json"
