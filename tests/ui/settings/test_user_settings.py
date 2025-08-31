"""
Copyright (c) Cutleast
"""

from copy import copy

import pytest
from cutleast_core_lib.test.utils import Utils
from cutleast_core_lib.ui.widgets.enum_dropdown import EnumDropdown
from PySide6.QtWidgets import QCheckBox, QLabel, QLineEdit
from pytestqt.qtbot import QtBot

from core.config.user_config import UserConfig
from core.translation_provider.provider_preference import ProviderPreference
from core.user_data.user_data import UserData
from core.utilities.game_language import GameLanguage
from tests.base_test import BaseTest
from ui.modinstance_selector.instance_selector_widget import InstanceSelectorWidget
from ui.settings.user_settings import UserSettings


class TestUserSettings(BaseTest):
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

    MODINSTANCE_SELECTOR: tuple[str, type[InstanceSelectorWidget]] = (
        "modinstance_selector",
        InstanceSelectorWidget,
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
    def user_settings(self, user_data: UserData, qtbot: QtBot) -> UserSettings:
        """
        Returns a new `UserSettings` instance for tests.
        """

        return UserSettings(user_data.user_config)

    # TODO: Fix this test
    @pytest.mark.skip(
        "Access violation when initializing the file dialog of a browse edit"
    )
    def test_initial(self, user_settings: UserSettings, user_data: UserData) -> None:
        """
        Tests the initial state of the `UserSettings` instance.
        """

        # given
        user_config: UserConfig = user_data.user_config

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

        assert (
            enable_interface_files_box.isChecked() == user_config.enable_interface_files
        )
        assert enable_scripts_box.isChecked() == user_config.enable_scripts
        assert enable_textures_box.isChecked() == user_config.enable_textures
        assert enable_sound_files_box.isChecked() == user_config.enable_sound_files

    # TODO: Fix this test
    @pytest.mark.skip(
        "Access violation when initializing the file dialog of a browse edit"
    )
    def test_apply(self, user_settings: UserSettings, user_data: UserData) -> None:
        """
        Tests the `apply` method of the `UserSettings` instance.
        """

        # given
        user_config: UserConfig = user_data.user_config
        old_config: UserConfig = copy(user_config)

        # when
        user_settings.apply(user_config)

        # then
        assert user_config == old_config
