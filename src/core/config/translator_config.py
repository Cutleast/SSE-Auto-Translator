"""
Copyright (c) Cutleast
"""

import logging
from typing import Optional

from core.translator_api import AVAILABLE_APIS
from core.translator_api.translator import Translator
from core.utilities.path import Path

from ._base_config import BaseConfig


class TranslatorConfig(BaseConfig):
    """
    Class for translator settings.
    """

    log = logging.getLogger("TranslatorConfig")

    def __init__(self, config_folder: Path):
        super().__init__(config_folder / "config.json", "translator")

    @property
    def translator(self) -> type[Translator]:
        """
        The translator API to use for machine translations.
        """

        translator_apis: dict[str, type[Translator]] = {
            translator.name: translator for translator in AVAILABLE_APIS
        }
        return translator_apis[self._settings["translator"]]

    @translator.setter
    def translator(self, translator: type[Translator]) -> None:
        TranslatorConfig.validate_value(translator, AVAILABLE_APIS)

        self._settings["translator"] = translator.name

    @property
    def api_key(self) -> Optional[str]:
        """
        The API key for the translator API.
        """

        return self._settings["api_key"]

    @api_key.setter
    def api_key(self, key: Optional[str]) -> None:
        if key is not None:
            TranslatorConfig.validate_type(key, str, may_be_none=True)

        self._settings["api_key"] = key

    @property
    def show_confirmation_dialogs(self) -> bool:
        """
        Whether to ask for confirmation before starting a machine translation.
        """

        return self._settings["show_confirmation_dialogs"]

    @show_confirmation_dialogs.setter
    def show_confirmation_dialogs(self, value: bool) -> None:
        TranslatorConfig.validate_type(value, bool)

        self._settings["show_confirmation_dialogs"] = value
