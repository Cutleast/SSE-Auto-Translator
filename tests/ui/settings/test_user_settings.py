"""
Copyright (c) Cutleast
"""

from copy import copy

import pytest
from cutleast_core_lib.test.utils import Utils
from cutleast_core_lib.ui.widgets.enum_dropdown import EnumDropdown
from mod_manager_lib.ui.instance_selector.instance_selector_widget import (
    InstanceSelectorWidget,
)
from PySide6.QtWidgets import QCheckBox, QLabel, QLineEdit
from pytestqt.qtbot import QtBot

from core.config.user_config import UserConfig
from core.translation_provider.provider_preference import ProviderPreference
from core.user_data.user_data import UserData
from core.utilities.game_language import GameLanguage
from tests.base_test import BaseTest
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

    @pytest.fixture
    def user_settings(self, user_data: UserData, qtbot: QtBot) -> UserSettings:
        """
        Returns a new `UserSettings` instance for tests.
        """

        return UserSettings(user_data.user_config)

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

        # then
        assert lang_box.getCurrentValue() == user_config.language
        assert source_label.isEnabled() == (user_config.language == GameLanguage.French)
        assert source_box.isEnabled() == (user_config.language == GameLanguage.French)
        assert source_box.getCurrentValue() == user_config.provider_preference
        assert api_key_entry.text() == user_config.api_key
        assert masterlist_box.isChecked() == user_config.use_masterlist

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
