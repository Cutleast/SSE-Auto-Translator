"""
Copyright (c) Cutleast
"""

from copy import copy

import pytest
from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel, QLineEdit

from app import App
from core.config.user_config import UserConfig
from core.mod_managers.mod_manager import ModManager
from core.translation_provider.provider_preference import ProviderPreference
from core.utilities.game_language import GameLanguage
from tests.app_test import AppTest
from tests.utils import Utils
from ui.settings.user_settings import UserSettings
from ui.widgets.browse_edit import BrowseLineEdit
from ui.widgets.enum_dropdown import EnumDropdown

from ..ui_test import UiTest


class TestUserSettings(UiTest, AppTest):
    """
    Tests `ui.settings.user_settings.UserSettings`.
    """

    LANG_BOX: tuple[str, type[EnumDropdown[GameLanguage]]] = (
        "lang_box",
        EnumDropdown[GameLanguage],
    )
    SOURCE_LABEL: tuple[str, type[QLabel]] = "source_label", QLabel
    SOURCE_BOX: tuple[str, type[EnumDropdown[ProviderPreference]]] = (
        "source_box",
        EnumDropdown[ProviderPreference],
    )
    API_KEY_ENTRY: tuple[str, type[QLineEdit]] = "api_key_entry", QLineEdit
    MASTERLIST_BOX: tuple[str, type[QCheckBox]] = "masterlist_box", QCheckBox

    MOD_MANAGER_BOX: tuple[str, type[EnumDropdown[ModManager.Type]]] = (
        "mod_manager_box",
        EnumDropdown[ModManager.Type],
    )
    MODINSTANCE_BOX: tuple[str, type[QComboBox]] = "modinstance_box", QComboBox
    INSTANCE_PROFILE_LABEL: tuple[str, type[QLabel]] = "instance_profile_label", QLabel
    INSTANCE_PROFILE_BOX: tuple[str, type[QComboBox]] = (
        "instance_profile_box",
        QComboBox,
    )
    INSTANCE_PATH_LABEL: tuple[str, type[QLabel]] = "instance_path_label", QLabel
    INSTANCE_PATH_ENTRY: tuple[str, type[BrowseLineEdit]] = (
        "instance_path_entry",
        BrowseLineEdit,
    )

    ENABLE_INTERFACE_FILES_BOX: tuple[str, type[QCheckBox]] = (
        "enable_interface_files_box",
        QCheckBox,
    )
    ENABLE_SCRIPTS_BOX: tuple[str, type[QCheckBox]] = "enable_scripts_box", QCheckBox
    ENABLE_TEXTURES_BOX: tuple[str, type[QCheckBox]] = "enable_textures_box", QCheckBox
    ENABLE_SOUND_FILES_BOX: tuple[str, type[QCheckBox]] = (
        "enable_sound_files_box",
        QCheckBox,
    )

    @pytest.fixture
    def user_settings(self, app_context: App) -> UserSettings:
        """
        Returns a new `UserSettings` instance for the given `App` instance.
        """

        return UserSettings(app_context.user_config, self.cache())

    def test_initial(self, user_settings: UserSettings, app_context: App) -> None:
        """
        Tests the initial state of the `UserSettings` instance.
        """

        # given
        user_config: UserConfig = app_context.user_config

        lang_box: EnumDropdown[GameLanguage] = Utils.get_private_field(
            user_settings, *TestUserSettings.LANG_BOX
        )
        source_label: QLabel = Utils.get_private_field(
            user_settings, *TestUserSettings.SOURCE_LABEL
        )
        source_box: EnumDropdown[ProviderPreference] = Utils.get_private_field(
            user_settings, *TestUserSettings.SOURCE_BOX
        )
        api_key_entry: QLineEdit = Utils.get_private_field(
            user_settings, *TestUserSettings.API_KEY_ENTRY
        )
        masterlist_box: QCheckBox = Utils.get_private_field(
            user_settings, *TestUserSettings.MASTERLIST_BOX
        )

        mod_manager_box: EnumDropdown[ModManager.Type] = Utils.get_private_field(
            user_settings, *TestUserSettings.MOD_MANAGER_BOX
        )
        modinstance_box: QComboBox = Utils.get_private_field(
            user_settings, *TestUserSettings.MODINSTANCE_BOX
        )
        instance_profile_label: QLabel = Utils.get_private_field(
            user_settings, *TestUserSettings.INSTANCE_PROFILE_LABEL
        )
        instance_profile_box: QComboBox = Utils.get_private_field(
            user_settings, *TestUserSettings.INSTANCE_PROFILE_BOX
        )
        instance_path_label: QLabel = Utils.get_private_field(
            user_settings, *TestUserSettings.INSTANCE_PATH_LABEL
        )
        instance_path_entry: BrowseLineEdit = Utils.get_private_field(
            user_settings, *TestUserSettings.INSTANCE_PATH_ENTRY
        )

        enable_interface_files_box: QCheckBox = Utils.get_private_field(
            user_settings, *TestUserSettings.ENABLE_INTERFACE_FILES_BOX
        )
        enable_scripts_box: QCheckBox = Utils.get_private_field(
            user_settings, *TestUserSettings.ENABLE_SCRIPTS_BOX
        )
        enable_textures_box: QCheckBox = Utils.get_private_field(
            user_settings, *TestUserSettings.ENABLE_TEXTURES_BOX
        )
        enable_sound_files_box: QCheckBox = Utils.get_private_field(
            user_settings, *TestUserSettings.ENABLE_SOUND_FILES_BOX
        )

        # then
        assert lang_box.getCurrentValue() == user_config.language
        assert source_label.isEnabled() == (user_config.language == GameLanguage.French)
        assert source_box.isEnabled() == (user_config.language == GameLanguage.French)
        assert source_box.getCurrentValue() == user_config.provider_preference
        assert api_key_entry.text() == user_config.api_key
        assert masterlist_box.isChecked() == user_config.use_masterlist

        assert mod_manager_box.getCurrentValue() == user_config.mod_manager
        assert modinstance_box.currentText() == user_config.modinstance
        assert instance_profile_label.isEnabled() == (
            user_config.mod_manager == ModManager.Type.ModOrganizer
        )
        assert instance_profile_box.isEnabled() == (
            user_config.mod_manager == ModManager.Type.ModOrganizer
        )
        assert instance_profile_box.currentText() == (
            (user_config.instance_profile or "Default")
            if user_config.mod_manager == ModManager.Type.ModOrganizer
            else user_config.instance_profile
        )
        assert instance_path_label.isEnabled() == (
            user_config.modinstance == "Portable"
        )
        assert instance_path_entry.isEnabled() == (
            user_config.modinstance == "Portable"
        )
        assert instance_path_entry.text() == str(user_config.instance_path or "")

        assert (
            enable_interface_files_box.isChecked() == user_config.enable_interface_files
        )
        assert enable_scripts_box.isChecked() == user_config.enable_scripts
        assert enable_textures_box.isChecked() == user_config.enable_textures
        assert enable_sound_files_box.isChecked() == user_config.enable_sound_files

    def test_apply(self, user_settings: UserSettings, app_context: App) -> None:
        """
        Tests the `apply` method of the `UserSettings` instance.
        """

        # given
        user_config: UserConfig = app_context.user_config
        old_config: UserConfig = copy(user_config)

        # when
        user_settings.apply(user_config)

        # then
        assert user_config == old_config
