"""
Copyright (c) Cutleast
"""

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

    user_config: UserConfig
    """The user configuration."""

    translator_config: TranslatorConfig
    """The API translator configuration."""

    database: TranslationDatabase
    """The translation database for the configured language."""

    modinstance: ModInstance
    """The configured modinstance."""

    masterlist: Masterlist
    """The configured masterlist."""
