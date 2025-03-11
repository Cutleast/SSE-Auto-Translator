"""
Copyright (c) Cutleast
"""

import logging
from typing import Optional

from core.mod_managers import SUPPORTED_MOD_MANAGERS
from core.mod_managers.mod_manager import ModManager
from core.translation_provider.provider_preference import ProviderPreference
from core.utilities.constants import SUPPORTED_LANGS
from core.utilities.path import Path

from ._base_config import BaseConfig


class UserConfig(BaseConfig):
    """
    Class for user settings.
    """

    log = logging.getLogger("UserConfig")

    def __init__(self, config_folder: Path):
        super().__init__(config_folder / "config.json", "user")

    @property
    def language(self) -> str:
        """
        Target language of the game.
        """

        return self._settings["language"]

    @language.setter
    def language(self, value: str) -> None:
        UserConfig.validate_type(value, str)
        UserConfig.validate_value(
            value, [lang[0].capitalize() for lang in SUPPORTED_LANGS]
        )

        self._settings["language"] = value

    @property
    def api_key(self) -> str:
        """
        API key for Nexus Mods.
        """

        return self._settings["api_key"]

    @api_key.setter
    def api_key(self, value: str) -> None:
        from core.translation_provider.nm_api.nm_api import NexusModsApi
        from core.translation_provider.provider_manager import ProviderManager

        UserConfig.validate_type(value, str)
        UserConfig.validate_value(
            value,
            lambda value: ProviderManager.get_provider(NexusModsApi).is_api_key_valid(
                value
            ),
        )

        self._settings["api_key"] = value

    @property
    def mod_manager(self) -> type[ModManager]:
        """
        Mod manager to use.
        """

        mod_managers: dict[str, type[ModManager]] = {
            mod_manager.name: mod_manager for mod_manager in SUPPORTED_MOD_MANAGERS
        }
        return mod_managers[self._settings["mod_manager"]]

    @mod_manager.setter
    def mod_manager(self, value: type[ModManager]) -> None:
        # UserConfig.validate_type(value, type[ModManager])
        UserConfig.validate_value(value, SUPPORTED_MOD_MANAGERS)

        self._settings["mod_manager"] = value.name

    @property
    def modinstance(self) -> str:
        """
        Mod instance to load.
        """

        return self._settings["modinstance"]

    @modinstance.setter
    def modinstance(self, value: str) -> None:
        UserConfig.validate_type(value, str)

        self._settings["modinstance"] = value

    @property
    def instance_profile(self) -> str:
        """
        Instance profile to load.
        """

        return self._settings["instance_profile"]

    @instance_profile.setter
    def instance_profile(self, value: str) -> None:
        UserConfig.validate_type(value, str)

        self._settings["instance_profile"] = value

    @property
    def instance_path(self) -> Optional[Path]:
        """
        Path to portable MO2 instance.
        """

        str_path: Optional[str] = self._settings["instance_path"]

        if str_path is not None:
            return Path(str_path)
        else:
            return None

    @instance_path.setter
    def instance_path(self, value: Optional[Path]) -> None:
        UserConfig.validate_type(value, Path, may_be_none=True)
        UserConfig.validate_value(value, lambda value: value.is_dir(), may_be_none=True)  # type: ignore

        self._settings["instance_path"] = str(value)

    @property
    def use_masterlist(self) -> bool:
        """
        Whether to use the masterlist.
        """

        return self._settings["use_masterlist"]

    @use_masterlist.setter
    def use_masterlist(self, value: bool) -> None:
        UserConfig.validate_type(value, bool)

        self._settings["use_masterlist"] = value

    @property
    def provider_preference(self) -> ProviderPreference:
        """
        Preferred translation provider.
        """

        return ProviderPreference[self._settings["provider_preference"]]

    @provider_preference.setter
    def provider_preference(self, value: ProviderPreference) -> None:
        UserConfig.validate_type(value, ProviderPreference)

        self._settings["provider_preference"] = value.name

    @property
    def enable_interface_files(self) -> bool:
        """
        Whether to include interface files when importing translations.
        """

        return self._settings["enable_interface_files"]

    @enable_interface_files.setter
    def enable_interface_files(self, value: bool) -> None:
        UserConfig.validate_type(value, bool)

        self._settings["enable_interface_files"] = value

    @property
    def enable_scripts(self) -> bool:
        """
        Whether to include scripts when importing translations.
        """

        return self._settings["enable_scripts"]

    @enable_scripts.setter
    def enable_scripts(self, value: bool) -> None:
        UserConfig.validate_type(value, bool)

        self._settings["enable_scripts"] = value

    @property
    def enable_textures(self) -> bool:
        """
        Whether to include textures when importing translations.
        """

        return self._settings["enable_textures"]

    @enable_textures.setter
    def enable_textures(self, value: bool) -> None:
        UserConfig.validate_type(value, bool)

        self._settings["enable_textures"] = value

    @property
    def enable_sound_files(self) -> bool:
        """
        Whether to include sound files when importing translations.
        """

        return self._settings["enable_sound_files"]

    @enable_sound_files.setter
    def enable_sound_files(self, value: bool) -> None:
        UserConfig.validate_type(value, bool)

        self._settings["enable_sound_files"] = value

    @property
    def author_blacklist(self) -> list[str]:
        """
        List of authors to ignore when scanning for translations.
        """

        return self._settings["author_blacklist"]

    @author_blacklist.setter
    def author_blacklist(self, value: list[str]) -> None:
        # UserConfig.validate_type(value, list[str])
        UserConfig.validate_value(
            value,
            lambda value: all(isinstance(author, str) for author in value),  # type: ignore
        )

        self._settings["author_blacklist"] = value

    @property
    def plugin_ignorelist(self) -> list[str]:
        """
        List of plugins that are completly ignored.
        """

        return self._settings["plugin_ignorelist"]

    @plugin_ignorelist.setter
    def plugin_ignorelist(self, value: list[str]) -> None:
        # UserConfig.validate_type(value, list[str])
        UserConfig.validate_value(
            value,
            lambda value: all(isinstance(plugin, str) for plugin in value),  # type: ignore
        )

        self._settings["plugin_ignorelist"] = value
