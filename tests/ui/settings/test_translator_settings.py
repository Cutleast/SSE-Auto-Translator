"""
Copyright (c) Cutleast
"""

from copy import copy

import pytest
from cutleast_core_lib.core.config.exceptions import ConfigValidationError
from cutleast_core_lib.test.utils import Utils
from cutleast_core_lib.ui.widgets.enum_selector import EnumSelector
from cutleast_core_lib.ui.widgets.key_edit import KeyLineEdit
from PySide6.QtWidgets import QCheckBox, QGroupBox
from pytestqt.qtbot import QtBot

from core.config.translator_config import TranslatorConfig
from core.translator.apis import TranslatorApi
from core.user_data.user_data import UserData
from tests.base_test import BaseTest
from ui.settings.translator_settings import TranslatorSettings


class TestTranslatorSettings(BaseTest):
    """
    Tests `ui.settings.translator_settings.TranslatorSettings`.
    """

    API_SELECTOR: tuple[str, type[EnumSelector[TranslatorApi]]] = (
        "api_selector",
        EnumSelector[TranslatorApi],
    )
    DEEPL_GROUP: tuple[str, type[QGroupBox]] = "deepl_group", QGroupBox
    DEEPL_API_KEY_ENTRY: tuple[str, type[KeyLineEdit]] = (
        "deepl_api_key_entry",
        KeyLineEdit,
    )

    SHOW_CONFIRMATIONS_BOX: tuple[str, type[QCheckBox]] = (
        "show_confirmations_box",
        QCheckBox,
    )

    @pytest.fixture
    def translator_settings(
        self, user_data: UserData, qtbot: QtBot
    ) -> TranslatorSettings:
        """
        Returns a new `TranslatorSettings` instance for tests.
        """

        translator_settings = TranslatorSettings(user_data.translator_config_manager)
        qtbot.addWidget(translator_settings)

        return translator_settings

    def test_initial(
        self, translator_settings: TranslatorSettings, user_data: UserData
    ) -> None:
        """
        Tests the initial state of the `TranslatorSettings` instance.
        """

        # given
        translator_config: TranslatorConfig = user_data.translator_config

        api_selector: EnumSelector[TranslatorApi] = Utils.get_private_field(
            translator_settings, *TestTranslatorSettings.API_SELECTOR
        )
        deepl_group: QGroupBox = Utils.get_private_field(
            translator_settings, *TestTranslatorSettings.DEEPL_GROUP
        )
        deepl_api_key_entry: KeyLineEdit = Utils.get_private_field(
            translator_settings, *TestTranslatorSettings.DEEPL_API_KEY_ENTRY
        )

        show_confirmations_box: QCheckBox = Utils.get_private_field(
            translator_settings, *TestTranslatorSettings.SHOW_CONFIRMATIONS_BOX
        )

        # then
        assert api_selector.getCurrentValue() == translator_config.translator
        assert (not deepl_group.isHidden()) == (
            translator_config.translator == TranslatorApi.DeepL
        )
        assert (
            deepl_api_key_entry.text().strip() or None
        ) == translator_config.deepl_api_key

        assert (
            show_confirmations_box.isChecked()
            == translator_config.show_confirmation_dialogs
        )

    def test_apply(
        self, translator_settings: TranslatorSettings, user_data: UserData
    ) -> None:
        """
        Tests the `apply` method of the `AppSettings` instance.
        """

        # given
        translator_config: TranslatorConfig = user_data.translator_config
        old_config: TranslatorConfig = copy(translator_config)

        # when
        translator_settings.apply()

        # then
        assert translator_config == old_config

    def test_validate_raises_for_missing_deepl_api_key(
        self, translator_settings: TranslatorSettings
    ) -> None:
        """
        Tests that `validate` requires an API key for DeepL.
        """

        # given
        api_selector: EnumSelector[TranslatorApi] = Utils.get_private_field(
            translator_settings, *TestTranslatorSettings.API_SELECTOR
        )
        deepl_api_key_entry: KeyLineEdit = Utils.get_private_field(
            translator_settings, *TestTranslatorSettings.DEEPL_API_KEY_ENTRY
        )
        api_selector.setCurrentValue(TranslatorApi.DeepL)
        deepl_api_key_entry.setText("   ")

        # when / then
        with pytest.raises(ConfigValidationError, match="API key is required for DeepL"):
            translator_settings.validate()
