"""
Copyright (c) Cutleast
"""

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from core.config.translator_config import TranslatorConfig
from core.config.user_config import UserConfig
from core.database.database import TranslationDatabase
from core.masterlist.masterlist import Masterlist
from core.mod_instance.mod_instance import ModInstance


@dataclass(frozen=True, kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class UserData:
    """
    Dataclass for holding the loaded user data.
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
