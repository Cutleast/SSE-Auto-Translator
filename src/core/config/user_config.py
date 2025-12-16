"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Annotated, Optional, override

from cutleast_core_lib.core.config.base_config import BaseConfig
from mod_manager_lib.core.mod_manager.modorganizer.mo2_instance_info import (
    MO2InstanceInfo,
)
from mod_manager_lib.core.mod_manager.vortex.profile_info import ProfileInfo
from pydantic import Field

from core.translation_provider.provider_preference import ProviderPreference
from core.utilities.game_language import GameLanguage


class UserConfig(BaseConfig):
    """
    Class for user settings.
    """

    language: GameLanguage
    """Target language of the game."""

    api_key: Annotated[str, BaseConfig.PropertyMarker.ExcludeFromLogging]
    """API key for Nexus Mods."""

    modinstance: Optional[MO2InstanceInfo | ProfileInfo] = Field(
        default=None, discriminator="mod_manager"
    )
    """Mod instance to load."""

    use_masterlist: bool = True
    """Whether to use the masterlist."""

    provider_preference: ProviderPreference = ProviderPreference.OnlyNexusMods
    """Preferred translation provider."""

    use_dynamic_string_distributor: bool = True
    """
    Whether to export strings from plugin files in the DynamicStringDistributor format.
    """

    author_blacklist: list[str] = []
    """List of authors to ignore when scanning for translations."""

    modfile_ignorelist: list[str] = []
    """List of modfiles that are completely ignored."""

    parse_bsa_archives: bool = True
    """Whether to parse the BSA archives of a modlist."""

    @staticmethod
    def create(user_config_path: Path) -> "UserConfig":
        """
        Creates a new blank user config. Explicitely setting the attributes is strongly
        recommended.

        Args:
            user_config_path (Path): Path to folder with user configuration.

        Returns:
            UserConfig: The created user config
        """

        config = UserConfig(
            _config_path=user_config_path,
            language=GameLanguage.German,
            api_key="",
            modinstance=None,
        )
        config._config_path = user_config_path

        return config

    @override
    @staticmethod
    def get_config_name() -> str:
        return "user/config.json"
