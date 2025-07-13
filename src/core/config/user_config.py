"""
Copyright (c) Cutleast
"""

from pathlib import Path
from typing import Annotated, Optional, override

from core.mod_managers.mod_manager import ModManager
from core.translation_provider.provider_preference import ProviderPreference
from core.utilities.game_language import GameLanguage

from ._base_config import BaseConfig


class UserConfig(BaseConfig):
    """
    Class for user settings.
    """

    language: GameLanguage
    """Target language of the game."""

    api_key: Annotated[str, BaseConfig.PropertyMarker.ExcludeFromLogging]
    """API key for Nexus Mods."""

    mod_manager: ModManager.Type
    """Mod manager to use."""

    modinstance: str
    """Mod instance to load."""

    instance_profile: Optional[str] = None
    """Instance profile to load."""

    instance_path: Optional[Path] = None
    """Path to portable MO2 instance."""

    use_masterlist: bool = True
    """Whether to use the masterlist."""

    provider_preference: ProviderPreference = ProviderPreference.OnlyNexusMods
    """Preferred translation provider."""

    enable_interface_files: bool = True
    """Whether to include interface files when importing translations."""

    enable_scripts: bool = False
    """Whether to include scripts when importing translations."""

    enable_textures: bool = False
    """Whether to include textures when importing translations."""

    enable_sound_files: bool = False
    """Whether to include sound files when importing translations."""

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
            mod_manager=ModManager.Type.ModOrganizer,
            modinstance="",
        )
        config._config_path = user_config_path

        return config

    @override
    @staticmethod
    def get_config_name() -> str:
        return "user/config.json"
