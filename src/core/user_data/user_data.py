"""
Copyright (c) Cutleast
"""

from cutleast_core_lib.core.config.manager import ConfigManager
from pydantic import BaseModel

from core.config.translator_config import TranslatorConfig
from core.config.user_config import UserConfig
from core.database.database import TranslationDatabase
from core.masterlist.masterlist import Masterlist
from core.mod_instance.mod_instance import ModInstance


class UserData(BaseModel, frozen=True, arbitrary_types_allowed=True):
    """
    Model for holding the loaded user data.
    """

    user_config_manager: ConfigManager[UserConfig]
    """The manager of the user configuration."""

    translator_config_manager: ConfigManager[TranslatorConfig]
    """The manager of the API translator configuration."""

    database: TranslationDatabase
    """The translation database for the configured language."""

    mod_instance: ModInstance
    """The configured mod instance."""

    masterlist: Masterlist
    """The configured masterlist."""

    @property
    def user_config(self) -> UserConfig:
        """The user configuration."""

        return self.user_config_manager.config

    @property
    def translator_config(self) -> TranslatorConfig:
        """The API translator configuration."""

        return self.translator_config_manager.config
